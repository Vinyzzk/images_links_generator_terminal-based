from time import sleep
import json
import os
import requests
import json
import pandas as pd
import openpyxl
from PIL import Image
import base64


def check_token():
    global token

    # Check ImgBB API Token
    with open("configs/config.json", "r") as file:
        data = json.load(file)
        token = data.get("token")

    if not token:
        token = input("Informe o ImgBB API Token: ")
        data["token"] = token
        with open("configs/config.json", "w") as file:
            json.dump(data, file, indent=4)

    # TODO: adicionar uma verificacao se o token é valido ou nao, e pedir para inserir novamente
    # TODO: adicionaru um botao para readicionar o token
    # TODO: adicionar logs terminal-based, e retorno de interface de usuario conforme os arquivos forem sendo convertidos e upados
    
def default_folder():
    os.makedirs("images", exist_ok=True)


def create_folders():
    os.makedirs("converted", exist_ok=True)
    for folder in os.listdir("images"):
        os.makedirs(f"converted/{folder}", exist_ok=True)


def convert_images():
    for folder in os.listdir("images"):
        folder_path = os.path.join("images", folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                name, ext = os.path.splitext(file)
                print(name, ext)
                
                input_file_path = os.path.join(folder_path, file)
                output_folder_path = os.path.join("converted", folder)
                output_file_path = os.path.join(output_folder_path, f"{name}.jpeg" if ext != ".png" else f"{name}.png")

                if ext != ".png":
                    img = Image.open(input_file_path).convert("RGB")
                else:
                    img = Image.open(input_file_path).convert("RGBA")
                
                img.save(output_file_path)
                img.close()


def upload_images():
    data = []

    for folder in os.listdir("converted"):
        links = []
        links_bling_excel = []
        for img in os.listdir(f"converted/{folder}"):
            name, ext = os.path.splitext(img)
            if not img.endswith(".txt"):
                with open(f"converted/{folder}/{img}", "rb") as file:
                    url = "https://api.imgbb.com/1/upload"
                    payload = {
                        "key": token,
                        "image": base64.b64encode(file.read()),
                    }
                    res = requests.post(url, data=payload)
                    res = res.json()
                    res = res.get("data")
                    res = res.get("url")
                    links.append(f"{res}\n")
                    links_bling_excel.append(res)

        my_separator = "|"
        links.sort()  # Ordenar os links em ordem alfabética
        links_bling = my_separator.join(links)  # Separar os links com o separador definido
        links_bling_excel = my_separator.join(links_bling_excel)  # Separar os links com SKU com o separador definido
        
        with open(f"converted/{folder}/url.txt", "w+") as txt:
            txt.writelines(links)
        with open(f"converted/{folder}/url_bling.txt", "w+") as txt2:
            txt2.write(links_bling)

        data.append({"SKU": folder, "Links": links_bling_excel})

    df = pd.DataFrame(data)
    df.to_excel("converted/result.xlsx", index=False, engine="openpyxl")


def main():
    default_folder()
    check_token()
    create_folders()
    convert_images()
    upload_images()

main()