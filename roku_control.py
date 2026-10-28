#!/usr/bin/env python3
"""Control remoto para Roku TV (AOC u otra marca) usando ECP (External Control Protocol).

Debe ejecutarse desde un equipo conectado a la misma red Wi-Fi que el televisor.
Solo usa la biblioteca estándar de Python 3.

Ejemplos:
    python3 roku_control.py buscar
    python3 roku_control.py --ip 192.168.1.50 info
    python3 roku_control.py --ip 192.168.1.50 tecla Home
    python3 roku_control.py --ip 192.168.1.50 apps
    python3 roku_control.py --ip 192.168.1.50 abrir netflix
    python3 roku_control.py --ip 192.168.1.50 escribir "hola mundo"
    python3 roku_control.py --ip 192.168.1.50 interactivo
"""

import argparse
import re
import socket
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

PUERTO = 8060

# Atajos en español -> teclas ECP
ALIAS = {
    "inicio": "Home", "home": "Home",
    "arriba": "Up", "abajo": "Down", "izquierda": "Left", "derecha": "Right",
    "ok": "Select", "aceptar": "Select",
    "atras": "Back", "atrás": "Back", "volver": "Back",
    "play": "Play", "pausa": "Play", "rew": "Rev", "fwd": "Fwd",
    "repetir": "InstantReplay", "info": "Info", "opciones": "Info",
    "buscar": "Search",
    "vol+": "VolumeUp", "subir": "VolumeUp",
    "vol-": "VolumeDown", "bajar": "VolumeDown",
    "silencio": "VolumeMute", "mute": "VolumeMute",
    "apagar": "PowerOff", "encender": "PowerOn", "power": "Power",
    "canal+": "ChannelUp", "canal-": "ChannelDown",
    "hdmi1": "InputHDMI1", "hdmi2": "InputHDMI2", "hdmi3": "InputHDMI3",
    "hdmi4": "InputHDMI4", "antena": "InputTuner", "av": "InputAV1",
}

# Teclas del modo interactivo
TECLAS_INTERACTIVO = {
    "w": "Up", "s": "Down", "a": "Left", "d": "Right", "": "Select",
    "b": "Back", "h": "Home", "p": "Play", "+": "VolumeUp", "-": "VolumeDown",
    "m": "VolumeMute", "i": "Info", "o": "PowerOff", "e": "PowerOn",
}


def buscar_rokus(espera=3.0):
    """Descubre dispositivos Roku en la red local mediante SSDP."""
    mensaje = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        'MAN: "ssdp:discover"\r\n'
        "ST: roku:ecp\r\n"
        "MX: 2\r\n\r\n"
    ).encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(espera)
    sock.sendto(mensaje, ("239.255.255.250", 1900))
    encontrados = set()
    fin = time.time() + espera
    try:
        while time.time() < fin:
            datos, _ = sock.recvfrom(1024)
            m = re.search(r"LOCATION:\s*http://([\d.]+):(\d+)", datos.decode(errors="ignore"), re.I)
            if m:
                encontrados.add(m.group(1))
    except socket.timeout:
        pass
    finally:
        sock.close()
    return sorted(encontrados)


class Roku:
    def __init__(self, ip):
        self.base = f"http://{ip}:{PUERTO}"

    def _get(self, ruta):
        with urllib.request.urlopen(self.base + ruta, timeout=5) as r:
            return r.read()

    def _post(self, ruta):
        req = urllib.request.Request(self.base + ruta, data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status

    def tecla(self, nombre):
        nombre = ALIAS.get(nombre.lower(), nombre)
        self._post("/keypress/" + urllib.parse.quote(nombre))

    def escribir(self, texto):
        for c in texto:
            self._post("/keypress/Lit_" + urllib.parse.quote(c))

    def info(self):
        raiz = ET.fromstring(self._get("/query/device-info"))
        return {hijo.tag: hijo.text for hijo in raiz}

    def apps(self):
        raiz = ET.fromstring(self._get("/query/apps"))
        return [(a.get("id"), a.text) for a in raiz.findall("app")]

    def abrir(self, nombre_o_id):
        app_id = nombre_o_id
        if not nombre_o_id.isdigit():
            coincidencias = [i for i, n in self.apps() if nombre_o_id.lower() in (n or "").lower()]
            if not coincidencias:
                raise SystemExit(f"No encontré una app que coincida con '{nombre_o_id}'.")
            app_id = coincidencias[0]
        self._post(f"/launch/{app_id}")


def modo_interactivo(roku):
    print("Modo interactivo. Escribe una tecla y pulsa Enter:")
    print("  w/a/s/d = flechas   Enter = OK   b = atrás   h = inicio   p = play/pausa")
    print("  + / - = volumen   m = silencio   i = info   o = apagar   e = encender")
    print("  t <texto> = escribir texto   q = salir   (también acepta nombres ECP, p. ej. Rev)")
    while True:
        try:
            linea = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if linea == "q":
            return
        if linea.startswith("t "):
            roku.escribir(linea[2:])
            continue
        try:
            roku.tecla(TECLAS_INTERACTIVO.get(linea, linea))
        except Exception as e:
            print(f"Error: {e}")


def main():
    p = argparse.ArgumentParser(description="Control remoto para Roku TV vía ECP")
    p.add_argument("--ip", help="IP del televisor (si se omite, se busca automáticamente)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("buscar", help="Buscar televisores Roku en la red")
    sub.add_parser("info", help="Mostrar información del televisor")
    sub.add_parser("apps", help="Listar apps instaladas")
    sub.add_parser("interactivo", help="Control con el teclado")
    t = sub.add_parser("tecla", help="Enviar una o varias teclas (Home, Up, VolumeUp, inicio, ok...)")
    t.add_argument("teclas", nargs="+")
    a = sub.add_parser("abrir", help="Abrir una app por nombre o ID")
    a.add_argument("app")
    e = sub.add_parser("escribir", help="Escribir texto en un campo de búsqueda")
    e.add_argument("texto")
    args = p.parse_args()

    if args.cmd == "buscar":
        ips = buscar_rokus()
        print("\n".join(ips) if ips else "No se encontró ningún Roku. ¿Estás en la misma red Wi-Fi?")
        return

    ip = args.ip
    if not ip:
        ips = buscar_rokus()
        if not ips:
            sys.exit("No se encontró ningún Roku. Indica la IP con --ip (Configuración > Red > Acerca de).")
        ip = ips[0]
        print(f"Usando Roku en {ip}")
    roku = Roku(ip)

    if args.cmd == "info":
        d = roku.info()
        for k in ("friendly-device-name", "vendor-name", "model-name", "software-version", "power-mode"):
            print(f"{k}: {d.get(k)}")
    elif args.cmd == "apps":
        for app_id, nombre in roku.apps():
            print(f"{app_id:>8}  {nombre}")
    elif args.cmd == "tecla":
        for k in args.teclas:
            roku.tecla(k)
            time.sleep(0.15)
    elif args.cmd == "abrir":
        roku.abrir(args.app)
    elif args.cmd == "escribir":
        roku.escribir(args.texto)
    elif args.cmd == "interactivo":
        modo_interactivo(roku)


if __name__ == "__main__":
    main()
