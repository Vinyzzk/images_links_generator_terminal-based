from time import sleep
import json
import os
import requests
import pandas as pd
from PIL import Image
import base64
import urllib.request
import re

def create_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)

def download_images(url, folder_path, order):
    image_path = os.path.join(folder_path, f"{order}.jpg")
    urllib.request.urlretrieve(url, image_path)

def get_images(mlb):
    url = f"https://api.mercadolibre.com/items/{mlb}"
    response = requests.get(url)
    response_data = response.json()
    variations = response_data.get("variations", [])
    pictures = response_data.get("pictures", [])

    if variations:
        for variation in variations:
            variation_name_parts = [
                f"{attribute['name']}-{attribute['value_name']}"
                for attribute in variation.get("attribute_combinations", [])
            ]
            variation_name = re.sub(r'[^a-zA-Z-]', '', "-".join(variation_name_parts))
            folder_name = f"images/{mlb}-{variation_name}-{variation['id']}"
            create_folder(folder_name)

            for order, picture_id in enumerate(variation.get("picture_ids", []), start=1):
                url = f"https://http2.mlstatic.com/D_{picture_id}-F.jpg"
                download_images(url, folder_name, order)

    elif pictures:
        folder_name = f"images/{mlb}"
        create_folder(folder_name)

        for order, picture in enumerate(pictures, start=1):
            url = f"https://http2.mlstatic.com/D_{picture['id']}-F.jpg"
            download_images(url, folder_name, order)

    print(f"[+] Imagens do {mlb} baixadas!")


def get_images_by_list():
    df = pd.read_excel("mlbs.xlsx")
    mlbs = df["MLB"].values
    
    print("[!] Baixando imagens...")
    if not mlbs:
        print("[!] A lista de MLBs precisa ter ao menos um MLB.")
        input("Pressione ENTER para finalizar")
        return
    
    for mlb in mlbs:
        get_images(mlb)

    input("Pressione ENTER para finalizar")

def check_token():
    config_path = "configs/config.json"
    with open(config_path, "r") as file:
        data = json.load(file)
        token = data.get("token")

    if not token:
        token = input("Informe o ImgBB API Token: ")
        data["token"] = token
        with open(config_path, "w") as file:
            json.dump(data, file, indent=4)

    return token

def convert_images():
    create_folder("result")
    for folder in os.listdir("images"):
        folder_path = os.path.join("images", folder)
        output_folder_path = os.path.join("result", folder)
        create_folder(output_folder_path)

        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                name, ext = os.path.splitext(file)
                input_file_path = os.path.join(folder_path, file)
                output_file_path = os.path.join(output_folder_path, f"{name}.jpeg" if ext != ".png" else f"{name}.png")

                img = Image.open(input_file_path).convert("RGB" if ext != ".png" else "RGBA")
                img.save(output_file_path)
                img.close()
                print(f"[LOG] Imagem convertida: {name}")

def upload_images(token):
    data = []
    for folder in os.listdir("result"):
        folder_path = os.path.join("result", folder)
        if os.path.isdir(folder_path):
            links = []
            for img in os.listdir(folder_path):
                name, ext = os.path.splitext(img)
                if not img.endswith(".txt"):
                    with open(os.path.join(folder_path, img), "rb") as file:
                        payload = {"key": token, "image": base64.b64encode(file.read())}
                        res = requests.post("https://api.imgbb.com/1/upload", data=payload).json()
                        image_url = res["data"]["url"]
                        links.append(image_url)
                        print(f"[LOG] Imagem upada: {img} | Link: {image_url}")

            links_bling = "|".join(sorted(links))
            with open(os.path.join(folder_path, "url.txt"), "w") as txt:
                txt.writelines(f"{link}\n" for link in links)
            with open(os.path.join(folder_path, "url_bling.txt"), "w") as txt2:
                txt2.write(links_bling)

            data.append({"SKU": folder, "Links": links_bling})

    pd.DataFrame(data).to_excel("result/result.xlsx", index=False, engine="openpyxl")


def input_mlb():
    mlb = input("[>] Informe um MLB (ou digite 0 para sair): ").upper()
    if mlb == "0":
        return None
    return mlb if mlb.startswith("MLB") else input_mlb()

def main():
    create_folder("images")
    create_folder("result")
    token = check_token()
    
    option = int(input("""
Escolha uma opção:
[1] Converter e upar imagens
[2] Baixar imagens de um MLB específico
[3] Baixar, converter e upar imagens de um MLB
Seleção: """))
    
    if option == 1:
        convert_images()
        upload_images(token)

    elif option == 2:
        while True:
            mlb = input_mlb()
            if mlb is None:
                break
            get_images(mlb)

    elif option == 3:
        while True:
            mlb = input_mlb()
            if mlb is None:
                break
            get_images(mlb)
            convert_images()
            upload_images(token)

if __name__ == "__main__":
    main()
