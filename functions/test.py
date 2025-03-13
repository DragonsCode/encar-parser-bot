from bs4 import BeautifulSoup
from content import html_content

def extract_accident_summary(html_content):
    """
    Извлекает сводную информацию об истории аварий из HTML-страницы Encar.
    
    Аргументы:
        html_content (str): HTML-код страницы.
    
    Возвращает:
        dict: Словарь с заголовками и значениями из сводки.
    """
    # Парсим HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    summary = {}

    # Находим список сводки
    summary_list = soup.find('ul', class_='ReportAccidentSummary_list_accident__q6vLx')
    if not summary_list:
        print("Список сводки не найден в HTML.")
        return summary

    # Находим все элементы <li> в списке
    li_elements = summary_list.find_all('li')
    if not li_elements:
        print("Элементы списка не найдены.")
        return summary

    # Извлекаем данные из каждого <li>
    for li in li_elements:
        title_element = li.find('strong', class_='ReportAccidentSummary_tit__oxjum')
        value_element = li.find('span', class_='ReportAccidentSummary_txt__fVCew')

        # Проверяем, что оба элемента найдены
        if title_element and value_element:
            title = title_element.text.strip()
            value = value_element.text.strip()
            summary[title] = value
        else:
            print(f"Пропущен элемент списка: заголовок или значение отсутствует.")

    return summary

# Пример использования
# Предполагается, что html_content содержит ваш HTML-код
# html_content = "<ваш HTML здесь>"
summary = extract_accident_summary(html_content)
for title, value in summary.items():
    print(f"{title}: {value}")