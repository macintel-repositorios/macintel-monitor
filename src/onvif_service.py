import socket
import re
from xml.etree import ElementTree

# Tenta importar onvif se disponível
ONVIF_AVAILABLE = False
try:
    from onvif import ONVIFCamera
    ONVIF_AVAILABLE = True
except Exception as e:
    print(f"Aviso: Biblioteca 'onvif-zeep' não pôde ser inicializada: {e}")

def discover_onvif_devices(timeout=2.0):
    """
    Realiza a descoberta WS-Discovery enviando um pacote UDP Multicast 
    para o IP 239.255.255.250 na porta 3702.
    Retorna uma lista de IPs/Endereços das câmeras localizadas na rede.
    """
    # Mensagem de Probe padrão WS-Discovery
    probe_xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<Envelope xmlns:tds="http://www.onvif.org/ver10/device/wsdl" '
        'xmlns="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:dn="http://www.onvif.org/ver10/network/wsdl">'
        '<Header>'
        '<MessageID xmlns="http://schemas.xmlsoap.org/ws/2004/08/addressing">'
        'uuid:a89a0b16-5246-47b5-9db4-a953b0bc875b'
        '</MessageID>'
        '<To xmlns="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:schemas-xmlsoap.org:targets:reply</To>'
        '<Action xmlns="http://schemas.xmlsoap.org/ws/2004/08/addressing">'
        'http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe'
        '</Action>'
        '</Header>'
        '<Body>'
        '<Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery">'
        '<Types>tds:Device</Types>'
        '</Probe>'
        '</Body>'
        '</Envelope>'
    )
    
    devices = []
    
    # Configura socket UDP Multicast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(timeout)
    # Permite reutilizar porta
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Envia a requisição Multicast
        sock.sendto(probe_xml.encode('utf-8'), ('239.255.255.250', 3702))
        
        # Escuta as respostas até acabar o tempo limite
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                xml_str = data.decode('utf-8', errors='ignore')
                
                # Busca endereços HTTP da câmera na resposta (normalmente tags <XAddrs>)
                urls = re.findall(r'https?://[^\s<>"]+', xml_str)
                for url in urls:
                    if '/onvif/device_service' in url or 'device_service' in url:
                        if url not in devices:
                            devices.append(url)
            except socket.timeout:
                break
    except Exception as e:
        print(f"Erro na varredura WS-Discovery: {e}")
    finally:
        sock.close()
        
    return devices


def get_rtsp_stream_via_onvif(ip, port, user, password, channel=1, subtype="sub"):
    """
    Conecta na câmera via ONVIF, autentica e retorna a URL RTSP 
    correspondente ao canal e tipo de stream (main/sub).
    """
    if not ONVIF_AVAILABLE:
        return None
        
    try:
        # Inicializa a câmera ONVIF
        # Importante: o onvif-zeep precisa de WSDLs locais. O pacote padrão do pip já possui.
        cam = ONVIFCamera(ip, port, user, password)
        
        # Cria serviço de mídia
        media_service = cam.create_media_service()
        
        # Obtém os perfis de vídeo da câmera (Stream Profiles)
        profiles = media_service.GetProfiles()
        if not profiles:
            return None
            
        # Filtra os perfis
        # Geralmente cameras comuns têm 2 perfis (0 = Main, 1 = Sub)
        # DVRs multicanal expõem perfis associados a cada canal.
        target_profile = None
        
        # Se for DVR, tenta encontrar perfil baseado no canal
        # Ex: "Profile_1_SubStream" ou índice matemático
        channel_profiles = []
        for p in profiles:
            # Encontra todos os perfis contendo o número do canal ou correspondentes
            channel_profiles.append(p)
            
        if not channel_profiles:
            return None
            
        # Seleção simplificada inteligente:
        # Para câmeras single-channel:
        if len(profiles) <= 2:
            if subtype == "main":
                target_profile = profiles[0]
            else:
                target_profile = profiles[1] if len(profiles) > 1 else profiles[0]
        else:
            # Para DVRs multi-canal
            # Tentativa de casar perfil de canal específico
            # Ex: canal 2 sub -> busca perfil com índice correspondente
            sub_profiles = [p for p in profiles if "sub" in p.Name.lower() or "extra" in p.Name.lower()]
            main_profiles = [p for p in profiles if "main" in p.Name.lower() or "prime" in p.Name.lower()]
            
            if subtype == "sub" and len(sub_profiles) >= channel:
                target_profile = sub_profiles[channel - 1]
            elif subtype == "main" and len(main_profiles) >= channel:
                target_profile = main_profiles[channel - 1]
            else:
                # Fallback por índice
                idx = (channel - 1) * 2 + (1 if subtype == "sub" else 0)
                if idx < len(profiles):
                    target_profile = profiles[idx]
                else:
                    target_profile = profiles[0]
                    
        # Solicita a URI de Stream (RTSP) para o perfil selecionado
        stream_setup = {
            'Stream': 'RTP-Unicast',
            'Transport': {'Protocol': 'RTSP'}
        }
        
        uri_response = media_service.GetStreamUri({
            'StreamSetup': stream_setup,
            'ProfileToken': target_profile.token
        })
        
        # Retorna a URL final da resposta
        rtsp_url = uri_response.Uri
        
        # Injeta usuário/senha se a URL retornada não contiver
        if user and password and "rtsp://" in rtsp_url and f"{user}:" not in rtsp_url:
            rtsp_url = rtsp_url.replace("rtsp://", f"rtsp://{user}:{password}@")
            
        return rtsp_url
    except Exception as e:
        print(f"Erro ao obter URL via ONVIF ({ip}:{port}): {e}")
        return None
