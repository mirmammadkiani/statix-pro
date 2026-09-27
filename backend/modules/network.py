import socket
import io
import base64
import qrcode

def get_local_ip() -> str:
    """Returns the primary local network IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def generate_qr_base64(url: str) -> str:
    """Generates a base64 PNG data URI for the given URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64}"

def get_network_info(port: int = 8000):
    ip = get_local_ip()
    url = f"http://{ip}:{port}"
    qr_data = generate_qr_base64(url)
    return {
        "local_ip": ip,
        "port": port,
        "url": url,
        "qr_code": qr_data
    }
