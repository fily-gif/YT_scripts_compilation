import os
import logging
from multiprocessing import Pool
from functools import partial
import yt_dlp

# --- НАСТРОЙКИ СКРИПТА (изменяйте эти значения) ---

# Имя файла со списком ссылок для скачивания
LINKS_FILENAME = 'list.txt'
# Папка для сохранения музыки
MUSIC_PATH = './music/'
# Количество параллельных процессов (потоков)
WORKER_COUNT = 4

# ---------------------------------------------------


# --- НАСТРОЙКА ЛОГГИРОВАНИЯ ---
# Настраиваем логирование, чтобы безопасно писать ошибки из разных процессов в один файл.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()  # Вывод логов и в консоль
    ]
)

# --- ОСНОВНЫЕ ФУНКЦИИ ---

def ensure_directory_exists(directory: str):
    """Проверяет, существует ли директория, и создает её, если нет."""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Создана директория: {directory}")
    except OSError as e:
        logging.error(f"Не удалось создать директорию {directory}: {e}")
        exit(1) # Выходим, если не можем создать папку для сохранения

def get_links_from_file(filename: str) -> list[str]:
    """
    Читает ссылки из файла. Ожидается одна ссылка на строку.
    Пустые строки и пробелы по краям игнорируются.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            links = [line.strip().split()[0] for line in f if line.strip()]
        if not links:
            logging.warning(f"Файл {filename} пуст или не содержит ссылок.")
        return links
    except FileNotFoundError:
        logging.error(f"Файл не найден: {filename}")
        return []

def download_and_process_song(url: str, music_path: str):
    """
    Скачивает аудио по URL, конвертирует в MP3, встраивает обложку и метаданные,
    используя только yt-dlp.
    """
    if not url:
        return

    logging.info(f"Начинаю обработку: {url}")

    # Конфигурация для yt-dlp.
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(music_path, '%(uploader)s - %(title)s.%(ext)s'),
        'embed-thumbnail': True,
        'add-metadata': True,
        'noplaylist': True,
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info)
            logging.info(f"Успешно скачано и сохранено: {final_filename}")

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"Ошибка yt-dlp при загрузке {url}: {e}")
    except Exception as e:
        logging.error(f"Неизвестная ошибка при обработке {url}: {e}")

# --- ТОЧКА ВХОДА В СКРИПТ ---

def main():
    """
    Главная функция, которая запускает параллельную загрузку, используя заданные настройки.
    """
    # 1. Подготовка с использованием заданных настроек
    ensure_directory_exists(MUSIC_PATH)
    links = get_links_from_file(LINKS_FILENAME)

    if not links:
        logging.info("Нет ссылок для обработки. Завершение работы.")
        return

    logging.info(f"Найдено {len(links)} ссылок. Запускаю {WORKER_COUNT} параллельных процессов.")

    # 2. Запуск параллельной обработки
    worker_func = partial(download_and_process_song, music_path=MUSIC_PATH)

    with Pool(processes=WORKER_COUNT) as pool:
        pool.map(worker_func, links)

    logging.info("Все задачи завершены.")


if __name__ == '__main__':
    # Эта конструкция гарантирует, что код запустится только при исполнении файла,
    # а не при его импорте. Это обязательно для multiprocessing в Windows.
    main()
