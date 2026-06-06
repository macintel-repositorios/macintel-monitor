import os
import json

class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            # Padrão: config/cameras.json relativo ao diretório raiz do projeto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'config', 'cameras.json')
            
        self.config_path = config_path
        self.data = {"condominios": []}
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar cameras.json: {e}")
        else:
            print(f"Arquivo de configuração não encontrado em: {self.config_path}")

    def get_condominios(self):
        """Retorna a lista de todos os condomínios cadastrados."""
        return self.data.get("condominios", [])

    def get_cameras_for_condominio(self, condominio_id):
        """Retorna as câmeras de um condomínio específico."""
        for cond in self.get_condominios():
            if cond.get("id") == condominio_id:
                return cond.get("cameras", [])
        return []

    def get_dvr_by_name(self, condominio_id, dvr_name):
        """Retorna os dados de configuração de um DVR específico de um condomínio."""
        for cond in self.get_condominios():
            if cond.get("id") == condominio_id:
                for dvr in cond.get("dvrs", []):
                    if dvr.get("nome") == dvr_name:
                        return dvr
        return None

    def resolve_camera_url(self, condominio_id, camera):
        """
        Retorna a URL final da câmera.
        Se possuir uma 'url' explícita (ex: stream de teste ou RTSP direto), usa ela.
        Caso contrário, se tiver informações do DVR e canal, tenta resolver via ONVIF (se configurado)
        ou monta uma URL RTSP aproximada baseada em padrões.
        """
        if "url" in camera and camera["url"]:
            return camera["url"]
        
        # Tenta recuperar dados do DVR associado
        dvr_name = camera.get("dvr")
        canal = camera.get("canal", 1)
        stream_tipo = camera.get("stream_tipo", "sub") # 'main' ou 'sub' (fluxo extra)
        
        dvr = self.get_dvr_by_name(condominio_id, dvr_name)
        if not dvr:
            return None
        
        ip = dvr.get("ip")
        user = dvr.get("user", "admin")
        pwd = dvr.get("password", "")
        
        # Exemplo de URL de fallback (Intelbras/Dahua usam esta estrutura padrão de RTSP)
        # rtsp://usuario:senha@ip:554/cam/realmonitor?channel=X&subtype=Y
        # subtype=0 é Main Stream, subtype=1 é Sub-Stream (Extra)
        subtype = 1 if stream_tipo == "sub" else 0
        fallback_rtsp = f"rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel={canal}&subtype={subtype}"
        
        return fallback_rtsp

    def save_config(self):
        """Salva a estrutura self.data de volta no arquivo cameras.json."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
            return False

    def add_condominio(self, nome):
        """Adiciona um condomínio novo."""
        cond_id = "cond_" + nome.lower().replace(" ", "_")
        # Evita duplicação de ID
        for c in self.get_condominios():
            if c.get("id") == cond_id:
                cond_id += "_new"
                
        novo_cond = {
            "id": cond_id,
            "nome": nome,
            "dvrs": [],
            "cameras": []
        }
        self.data.setdefault("condominios", []).append(novo_cond)
        self.save_config()
        return cond_id

    def delete_condominio(self, cond_id):
        """Remove um condomínio pelo ID."""
        conds = self.get_condominios()
        self.data["condominios"] = [c for c in conds if c.get("id") != cond_id]
        self.save_config()

    def add_dvr(self, cond_id, dvr_data):
        """Adiciona ou atualiza um DVR em um condomínio."""
        for cond in self.get_condominios():
            if cond.get("id") == cond_id:
                # Remove duplicado com mesmo nome se existir
                cond["dvrs"] = [d for d in cond.get("dvrs", []) if d.get("nome") != dvr_data["nome"]]
                cond["dvrs"].append(dvr_data)
                self.save_config()
                return True
        return False

    def delete_dvr(self, cond_id, dvr_name):
        """Remove um DVR de um condomínio."""
        for cond in self.get_condominios():
            if cond.get("id") == cond_id:
                cond["dvrs"] = [d for d in cond.get("dvrs", []) if d.get("nome") != dvr_name]
                self.save_config()
                return True
        return False

    def add_camera(self, cond_id, camera_data):
        """Adiciona ou atualiza uma câmera em um condomínio."""
        for cond in self.get_condominios():
            if cond.get("id") == cond_id:
                # Remove duplicado com mesmo nome
                cond["cameras"] = [c for c in cond.get("cameras", []) if c.get("nome") != camera_data["nome"]]
                cond["cameras"].append(camera_data)
                self.save_config()
                return True
        return False

    def delete_camera(self, cond_id, camera_name):
        """Remove uma câmera de um condomínio."""
        for cond in self.get_condominios():
            if cond.get("id") == cond_id:
                cond["cameras"] = [c for c in cond.get("cameras", []) if c.get("nome") != camera_name]
                self.save_config()
                return True
        return False
