import subprocess
import os
import asyncio
import importlib
import zipfile
import requests
from io import BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# 🔑 Configuration du bot
TOKEN = "6331928281:AAFVw9csc-oXoz7Jwd9LoK9gumYqzQLT-mY"  # Remplace par ton token
AUTHORIZED_ID = 1726923679  # Remplace par ton ID Telegram
BASE_DIR = "scripts"
processes = {}
user_states = {}

# 📂 Création du dossier des scripts si non existant
os.makedirs(BASE_DIR, exist_ok=True)

# 📥 Télécharger les scripts depuis GitHub si BASE_DIR est vide
def fetch_scripts_from_github():
    if not os.listdir(BASE_DIR):
        print("📂 Dossier scripts vide. Téléchargement depuis GitHub...")

        github_zip_url = "https://github.com/nikle-bot789/AI-IMAGE-BOT/blob/cef9388b54500eb9acaf0ae67211543c7996f816/main.zip"  # 🔁 Remplace cette URL
        try:
            response = requests.get(github_zip_url)
            with zipfile.ZipFile(BytesIO(response.content)) as z:
                root_dir = z.namelist()[0]
                for file in z.namelist():
                    if file.startswith(root_dir + "scripts/") and file.endswith(".py"):
                        filename = os.path.basename(file)
                        if filename:
                            with z.open(file) as source_file, open(os.path.join(BASE_DIR, filename), "wb") as target_file:
                                target_file.write(source_file.read())
            print("✅ Scripts restaurés depuis GitHub.")
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des scripts : {e}")

fetch_scripts_from_github()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🎛️ Clavier principal
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Ajouter un script")],
        [KeyboardButton(text="▶️ Exécuter un script")],
        [KeyboardButton(text="🔄 Redémarrer tous")],
        [KeyboardButton(text="📜 Liste des scripts")],
        [KeyboardButton(text="❌ Arrêter et Supprimer un script")],
    ],
    resize_keyboard=True
)

# 🏁 Commande /start
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id != AUTHORIZED_ID:
        await message.reply("❌ Accès refusé !")
        return
    await message.reply("👋 Bienvenue ! Choisissez une action :", reply_markup=main_keyboard)

# ➕ Ajouter un script
@dp.message(lambda message: message.text == "➕ Ajouter un script")
async def prompt_add_script(message: types.Message):
    user_states[message.from_user.id] = "ajout_script"
    await message.reply("📤 Envoie-moi un fichier **.py** pour l'ajouter au système.")

@dp.message(lambda message: message.document and user_states.get(message.from_user.id) == "ajout_script")
async def handle_script_upload(message: types.Message):
    document = message.document

    if not document.file_name.endswith(".py"):
        await message.reply("⚠️ Seuls les fichiers `.py` sont acceptés.")
        return

    file_path = os.path.join(BASE_DIR, document.file_name)
    file = await bot.get_file(document.file_id)
    await bot.download_file(file.file_path, file_path)

    await message.reply(f"✅ Script **{document.file_name}** ajouté avec succès !")
    user_states.pop(message.from_user.id, None)

# Fonction pour vérifier les bibliothèques manquantes
def check_and_install_libraries(file_path):
    with open(file_path, 'r') as file:
        script_content = file.read()

    imports = [line for line in script_content.splitlines() if line.startswith("import") or line.startswith("from")]
    missing_libraries = []

    for imp in imports:
        try:
            if imp.startswith("import"):
                module = imp.split()[1]
                importlib.import_module(module)
            elif imp.startswith("from"):
                module = imp.split()[1]
                importlib.import_module(module)
        except ImportError:
            module = imp.split()[1]
            missing_libraries.append(module)

    if missing_libraries:
        for lib in missing_libraries:
            subprocess.run(["pip", "install", lib])

    return missing_libraries

# ▶️ Exécuter un script
@dp.message(lambda message: message.text == "▶️ Exécuter un script")
async def list_files_for_running(message: types.Message):
    user_states[message.from_user.id] = "execution"
    files = os.listdir(BASE_DIR)
    if not files:
        await message.reply("🚫 Aucun script trouvé.")
        return
    
    buttons = [KeyboardButton(text=file) for file in files]
    keyboard_layout = [buttons[i:i+4] for i in range(0, len(buttons), 4)]
    keyboard_layout.append([KeyboardButton(text="⬅️ Retour au menu")])

    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_layout, resize_keyboard=True)
    await message.reply("🔍 Sélectionne un script à exécuter :", reply_markup=keyboard)

@dp.message(lambda message: message.text in os.listdir(BASE_DIR))
async def handle_script_selection(message: types.Message):
    user_id = message.from_user.id
    filename = message.text
    file_path = os.path.join(BASE_DIR, filename)

    if user_states.get(user_id) == "execution":
        missing_libraries = check_and_install_libraries(file_path)
        
        if missing_libraries:
            await message.reply(f"⚠️ Bibliothèques manquantes et installées automatiquement :\n" + "\n".join(missing_libraries))
        else:
            await message.reply(f"✅ Toutes les bibliothèques sont déjà installées. Exécution du script...")

        await message.reply(f"🚀 Exécution du script {filename}...")

        process = await asyncio.create_subprocess_exec(
            'python', file_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        processes[filename] = process

        stdout, stderr = await process.communicate()

        if stdout:
            await message.reply(f"📤 **Sortie :**\n```\n{stdout.decode()}\n```", parse_mode="Markdown")
        if stderr:
            await message.reply(f"⚠️ **Erreurs :**\n```\n{stderr.decode()}\n```", parse_mode="Markdown")

        user_states.pop(user_id, None)

    elif user_states.get(user_id) == "suppression":
        if filename in processes:
            process = processes[filename]
            if process.returncode is None:
                process.terminate()
                try:
                    await process.wait(timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
                await message.reply(f"🔴 Le script {filename} a été arrêté.")

            del processes[filename]

        if os.path.exists(file_path):
            os.remove(file_path)
            await message.reply(f"✅ Le script {filename} a été supprimé avec succès.")
        else:
            await message.reply(f"⚠️ Le fichier {filename} n'existe plus.")

        user_states.pop(user_id, None)
    else:
        await message.reply("⚠️ Action inconnue, veuillez réessayer.")

# ❌ Arrêter et supprimer un script
@dp.message(lambda message: message.text == "❌ Arrêter et Supprimer un script")
async def stop_and_delete_script(message: types.Message):
    user_states[message.from_user.id] = "suppression"
    files = os.listdir(BASE_DIR)
    if not files:
        await message.reply("🚫 Aucun script trouvé à supprimer.")
        return
    
    buttons = [KeyboardButton(text=file) for file in files]
    keyboard_layout = [buttons[i:i+4] for i in range(0, len(buttons), 4)]
    keyboard_layout.append([KeyboardButton(text="⬅️ Retour au menu")])

    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_layout, resize_keyboard=True)
    await message.reply("🔍 Sélectionne un script à arrêter et supprimer :", reply_markup=keyboard)

# 🔄 Redémarrer tous les scripts
@dp.message(lambda message: message.text == "🔄 Redémarrer tous")
async def restart_all_codes(message: types.Message):
    for filename in list(processes.keys()):
        process = processes[filename]
        if process.returncode is None:
            process.terminate()
            try:
                await process.wait(timeout=5)
            except asyncio.TimeoutError:
                process.kill()
        del processes[filename]

    for filename in os.listdir(BASE_DIR):
        file_path = os.path.join(BASE_DIR, filename)
        process = await asyncio.create_subprocess_exec(
            'python', file_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        processes[filename] = process

    await message.reply("♻️ Tous les scripts ont été redémarrés.")

# 📜 Liste des scripts
@dp.message(lambda message: message.text == "📜 Liste des scripts")
async def list_codes(message: types.Message):
    files = os.listdir(BASE_DIR)
    if not files:
        await message.reply("🚫 Aucun script trouvé.")
        return

    status = {file: "🟢 Actif" if file in processes and processes[file].returncode is None else "🔴 Arrêté" for file in files}
    response = "\n".join([f"{file}: {state}" for file, state in status.items()])
    await message.reply(f"📂 Scripts disponibles :\n{response}")

# ⬅️ Retour au menu
@dp.message(lambda message: message.text == "⬅️ Retour au menu")
async def return_to_main_menu(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await message.reply("🏠 Retour au menu principal.", reply_markup=main_keyboard)

# 🚀 Lancement du bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
