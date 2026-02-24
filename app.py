import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
from docx import Document
from io import BytesIO

# --- ИНИЦИАЛИЗАЦИЯ ИЗ СЕКРЕТОВ ---
# Если файлов secrets нет, используем заглушки для теста
try:
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_KEY"]
except:
    APP_PASSWORD = "admin"  # пароль по умолчанию для теста
    DEEPSEEK_KEY = "your_key_here"

client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

def get_market_info(query):
    with DDGS() as ddgs:
        results = [r['body'] for r in ddgs.text(f"купить {query} цены рф 2026", max_results=15)]
    return "\n".join(results)

def create_docx(text):
    """Создание Word документа в памяти"""
    doc = Document()
    doc.add_heading('Отчет по подбору мотоцикла', 0)
    doc.add_paragraph(text)
    
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="MotoVibe Pro", page_icon="🏍️")

with st.sidebar:
    st.title("🔐 Доступ")
    password_input = st.text_input("Введите пароль", type="password")
    
    if password_input != APP_PASSWORD:
        st.error("Доступ ограничен.")
        st.stop()
    
    st.success("Доступ разрешен")
    st.divider()
    
    budget = st.number_input("Бюджет (руб)", min_value=50000, value=600000, step=50000)
    moto_class = st.selectbox("Класс", ["Naked", "Sport", "Cruiser", "Touring", "Enduro", "Classic"])
    city = st.text_input("Город", value="Москва")
    model_count = st.slider("Сколько моделей?", 3, 10, 15, 5)

st.title("🏍️ MotoVibe: Подбор и Анализ Рисков")

# Состояние для хранения ответа ИИ, чтобы кнопка скачивания не исчезала
if 'last_report' not in st.session_state:
    st.session_state.last_report = None

if st.button("Сгенерировать подбор"):
    with st.spinner('Ищем варианты...'):
        search_context = get_market_info(f"{moto_class} за {budget}")
        
        prompt = f"""
        Ты - эксперт по мотоциклам. Параметры: Бюджет {budget}р, Класс {moto_class}, Город {city}.
        Предложи {model_count} моделей. 
        Для каждой: 
        1. Ожидаемый год. 
        2. Риски (Япония <2006, Китай <2020 - детально по узлам).
        3. Предупреждение если > 600сс.
        4. Сервис в {city}.
        Контекст: {search_context}
        """
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            st.session_state.last_report = response.choices[0].message.content
        except Exception as e:
            st.error(f"Ошибка API: {e}")

# Если отчет готов, показываем его и даем скачать
if st.session_state.last_report:
    st.markdown("### Результаты анализа")
    st.markdown(st.session_state.last_report)
    
    docx_file = create_docx(st.session_state.last_report)
    
    st.download_button(
        label="📥 Скачать отчет в Word (.docx)",
        data=docx_file,
        file_name=f"moto_selection_{city}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
