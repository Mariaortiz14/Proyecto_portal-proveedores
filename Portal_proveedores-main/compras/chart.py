import random
months = [
    "Enero", "Febrero", "Marzo", "Abril",
    "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
colorPalette = ["#55efc4", "#81ecec", "#a29bfe", "#ffeaa7", "#fab1a0", "#ff7675", "#fd79a8"]
colorPrimary, colorSuccess, colorDanger = "#79aec8", colorPalette[0], colorPalette[5]


def get_year_dict():
    year_dict = dict()

    for month in months:
        year_dict[month] = 0

    return year_dict


def generate_color_palette(amount):
    palette = []

    i = 0
    while i < len(colorPalette) and len(palette) < amount:
        palette.append(colorPalette[i])
        i += 1
        if i == len(colorPalette) and len(palette) < amount:
            i = 0

    return palette

def generate_color_random():
    color = "#"
    for j in range(6):
        color += random.choice("0123456789ABCDEF")
    return color