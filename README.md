# Control remoto para Roku TV (AOC)

Script en Python para controlar un televisor Roku TV desde la computadora usando
el protocolo local de Roku (ECP, puerto 8060). No necesita instalar nada extra.

## Requisitos

1. Python 3 instalado.
2. La computadora y el televisor en **la misma red Wi-Fi**.
3. En el televisor: **Configuración > Sistema > Configuración avanzada del sistema >
   Control por apps móviles > Acceso a la red** → poner en **Predeterminado** o **Permisivo**.

## Uso

```bash
python3 roku_control.py buscar                       # encuentra la IP del televisor
python3 roku_control.py --ip 192.168.1.50 info       # nombre, modelo, estado
python3 roku_control.py --ip 192.168.1.50 tecla inicio
python3 roku_control.py --ip 192.168.1.50 tecla vol+ vol+ vol+
python3 roku_control.py --ip 192.168.1.50 apps       # lista las apps instaladas
python3 roku_control.py --ip 192.168.1.50 abrir youtube
python3 roku_control.py --ip 192.168.1.50 escribir "los simpson"
python3 roku_control.py --ip 192.168.1.50 tecla hdmi1
python3 roku_control.py --ip 192.168.1.50 interactivo   # control con el teclado
```

Si omites `--ip`, el script busca el televisor automáticamente.

Atajos de teclas: `inicio`, `arriba`, `abajo`, `izquierda`, `derecha`, `ok`, `atras`,
`play`, `vol+`, `vol-`, `silencio`, `apagar`, `encender`, `hdmi1`–`hdmi4`, `antena`.
También acepta cualquier nombre de tecla ECP (`Home`, `Rev`, `Fwd`, `InstantReplay`…).
