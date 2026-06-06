from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QLineEdit, QComboBox, QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import Qt
from src.config import ConfigManager

class InputDialog(QDialog):
    """Diálogo genérico simples para formulários rápidos."""
    def __init__(self, title, fields, parent=None, initial_values=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0;")
        self.layout = QVBoxLayout(self)
        self.form = QFormLayout()
        
        self.inputs = {}
        for name, field_type, label in fields:
            if field_type == "text":
                inp = QLineEdit(self)
                inp.setStyleSheet("background-color: #2b2b2b; color: #ffffff; border: 1px solid #444; padding: 5px;")
                if initial_values and name in initial_values:
                    inp.setText(str(initial_values[name]))
            elif field_type == "combo":
                inp = QComboBox(self)
                inp.setStyleSheet("background-color: #2b2b2b; color: #ffffff; border: 1px solid #444; padding: 5px;")
                # Se as opções forem passadas no label como tupla/lista
                options, text_label = label
                inp.addItems(options)
                label = text_label
                if initial_values and name in initial_values:
                    idx = inp.findText(str(initial_values[name]))
                    if idx >= 0:
                        inp.setCurrentIndex(idx)
            self.form.addRow(QLabel(label), inp)
            self.inputs[name] = inp
            
        self.layout.addLayout(self.form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.setStyleSheet("QPushButton { background-color: #2b2b2b; color: white; border: 1px solid #555; padding: 5px 15px; }")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def get_data(self):
        data = {}
        for name, inp in self.inputs.items():
            if isinstance(inp, QLineEdit):
                data[name] = inp.text()
            elif isinstance(inp, QComboBox):
                data[name] = inp.currentText()
        return data


class DeviceManagerDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuração de Dispositivos e Câmeras")
        self.resize(800, 500)
        self.config = config_manager
        self.selected_condo_id = None
        
        self.init_ui()
        self.load_condos()

    def init_ui(self):
        # Estilo escuro moderno
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
            }
            QWidget {
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                font-weight: bold;
            }
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #222;
            }
            QListWidget::item:hover {
                background-color: #242424;
            }
            QListWidget::item:selected {
                background-color: #0088cc;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #2d2d2d;
                background-color: #1a1a1a;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #242424;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-bottom-color: #1a1a1a;
            }
            QPushButton {
                background-color: #242424;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #00aaff;
            }
            QTableWidget {
                background-color: #1a1a1a;
                gridline-color: #222;
                border: none;
            }
            QHeaderView::section {
                background-color: #242424;
                color: #aaa;
                padding: 5px;
                border: 1px solid #1a1a1a;
                font-weight: bold;
            }
        """)

        main_layout = QHBoxLayout(self)
        
        # --- PAINEL ESQUERDO: Condomínios ---
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("CONDOMÍNIOS"))
        
        self.condo_list = QListWidget()
        self.condo_list.itemSelectionChanged.connect(self.on_condo_selected)
        left_panel.addWidget(self.condo_list)
        
        condo_btns = QHBoxLayout()
        self.add_condo_btn = QPushButton("+ Adicionar")
        self.add_condo_btn.clicked.connect(self.add_condo)
        self.del_condo_btn = QPushButton("- Remover")
        self.del_condo_btn.clicked.connect(self.delete_condo)
        
        condo_btns.addWidget(self.add_condo_btn)
        condo_btns.addWidget(self.del_condo_btn)
        left_panel.addLayout(condo_btns)
        
        main_layout.addLayout(left_panel, stretch=1)
        
        # --- PAINEL DIREITO: DVRs e Câmeras (Tabs) ---
        right_panel = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # Tab de DVRs
        dvr_tab = QWidget()
        dvr_layout = QVBoxLayout(dvr_tab)
        
        self.dvr_table = QTableWidget(0, 4)
        self.dvr_table.setHorizontalHeaderLabels(["Nome", "IP", "Porta", "Usuário"])
        self.dvr_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dvr_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dvr_table.setSelectionMode(QTableWidget.SingleSelection)
        dvr_layout.addWidget(self.dvr_table)
        
        dvr_btns = QHBoxLayout()
        self.scan_dvr_btn = QPushButton("🔍 Localizar na Rede")
        self.scan_dvr_btn.setToolTip("Procurar câmeras e DVRs compatíveis com ONVIF na rede local")
        self.scan_dvr_btn.clicked.connect(self.scan_network)
        self.add_dvr_btn = QPushButton("+ Adicionar DVR")
        self.add_dvr_btn.clicked.connect(self.add_dvr)
        self.edit_dvr_btn = QPushButton("Editar")
        self.edit_dvr_btn.clicked.connect(self.edit_dvr)
        self.del_dvr_btn = QPushButton("Remover")
        self.del_dvr_btn.clicked.connect(self.delete_dvr)
        
        dvr_btns.addWidget(self.scan_dvr_btn)
        dvr_btns.addWidget(self.add_dvr_btn)
        dvr_btns.addWidget(self.edit_dvr_btn)
        dvr_btns.addWidget(self.del_dvr_btn)
        dvr_layout.addLayout(dvr_btns)
        
        self.tabs.addTab(dvr_tab, "DVRs / Gravadores")
        
        # Tab de Câmeras
        cam_tab = QWidget()
        cam_layout = QVBoxLayout(cam_tab)
        
        self.cam_table = QTableWidget(0, 4)
        self.cam_table.setHorizontalHeaderLabels(["Nome Câmera", "DVR Associado", "Canal", "Tipo Fluxo"])
        self.cam_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cam_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cam_table.setSelectionMode(QTableWidget.SingleSelection)
        cam_layout.addWidget(self.cam_table)
        
        cam_btns = QHBoxLayout()
        self.add_cam_btn = QPushButton("+ Adicionar Câmera")
        self.add_cam_btn.clicked.connect(self.add_camera)
        self.edit_cam_btn = QPushButton("Editar")
        self.edit_cam_btn.clicked.connect(self.edit_camera)
        self.del_cam_btn = QPushButton("Remover")
        self.del_cam_btn.clicked.connect(self.delete_camera)
        
        cam_btns.addWidget(self.add_cam_btn)
        cam_btns.addWidget(self.edit_cam_btn)
        cam_btns.addWidget(self.del_cam_btn)
        cam_layout.addLayout(cam_btns)
        
        self.tabs.addTab(cam_tab, "Câmeras / Canais")
        
        right_panel.addWidget(self.tabs)
        main_layout.addLayout(right_panel, stretch=2)

    def load_condos(self):
        self.condo_list.clear()
        for c in self.config.get_condominios():
            item = QListWidgetItem(c.get("nome"))
            item.setData(Qt.UserRole, c.get("id"))
            self.condo_list.addItem(item)
            
        # Desativa abas se não houver condomínio selecionado
        self.tabs.setEnabled(False)

    def on_condo_selected(self):
        selected_items = self.condo_list.selectedItems()
        if not selected_items:
            self.selected_condo_id = None
            self.tabs.setEnabled(False)
            return
            
        self.selected_condo_id = selected_items[0].data(Qt.UserRole)
        self.tabs.setEnabled(True)
        self.refresh_dvr_table()
        self.refresh_camera_table()

    def refresh_dvr_table(self):
        self.dvr_table.setRowCount(0)
        conds = self.config.get_condominios()
        for cond in conds:
            if cond.get("id") == self.selected_condo_id:
                dvrs = cond.get("dvrs", [])
                for dvr in dvrs:
                    row = self.dvr_table.rowCount()
                    self.dvr_table.insertRow(row)
                    self.dvr_table.setItem(row, 0, QTableWidgetItem(dvr.get("nome", "")))
                    self.dvr_table.setItem(row, 1, QTableWidgetItem(dvr.get("ip", "")))
                    self.dvr_table.setItem(row, 2, QTableWidgetItem(str(dvr.get("onvif_port", 80))))
                    self.dvr_table.setItem(row, 3, QTableWidgetItem(dvr.get("user", "")))

    def refresh_camera_table(self):
        self.cam_table.setRowCount(0)
        conds = self.config.get_condominios()
        for cond in conds:
            if cond.get("id") == self.selected_condo_id:
                cameras = cond.get("cameras", [])
                for cam in cameras:
                    row = self.cam_table.rowCount()
                    self.cam_table.insertRow(row)
                    self.cam_table.setItem(row, 0, QTableWidgetItem(cam.get("nome", "")))
                    self.cam_table.setItem(row, 1, QTableWidgetItem(cam.get("dvr", "Direta (Sem DVR)")))
                    self.cam_table.setItem(row, 2, QTableWidgetItem(str(cam.get("canal", "-"))))
                    self.cam_table.setItem(row, 3, QTableWidgetItem(cam.get("stream_tipo", "sub")))

    # --- CRUD Condomínios ---
    def add_condo(self):
        fields = [("nome", "text", "Nome do Condomínio:")]
        dialog = InputDialog("Novo Condomínio", fields, self)
        if dialog.exec() == QDialog.Accepted:
            nome = dialog.get_data().get("nome")
            if nome:
                self.config.add_condominio(nome)
                self.load_condos()
                # Seleciona o novo condomínio
                for i in range(self.condo_list.count()):
                    if self.condo_list.item(i).text() == nome:
                        self.condo_list.setCurrentRow(i)
                        break

    def delete_condo(self):
        if not self.selected_condo_id:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            "Deseja realmente excluir este condomínio e todos os seus DVRs/Câmeras?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.delete_condominio(self.selected_condo_id)
            self.load_condos()

    # --- CRUD DVRs ---
    def get_dvr_fields(self):
        return [
            ("nome", "text", "Nome do DVR:"),
            ("ip", "text", "IP/Host:"),
            ("onvif_port", "text", "Porta ONVIF:"),
            ("user", "text", "Usuário:"),
            ("password", "text", "Senha:")
        ]

    def add_dvr(self):
        dialog = InputDialog("Novo DVR", self.get_dvr_fields(), self, initial_values={"onvif_port": 80, "user": "admin"})
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data["nome"] and data["ip"]:
                dvr_data = {
                    "nome": data["nome"],
                    "ip": data["ip"],
                    "onvif_port": int(data["onvif_port"]) if data["onvif_port"].isdigit() else 80,
                    "user": data["user"],
                    "password": data["password"]
                }
                self.config.add_dvr(self.selected_condo_id, dvr_data)
                self.refresh_dvr_table()

    def edit_dvr(self):
        curr_row = self.dvr_table.currentRow()
        if curr_row < 0:
            return
        
        dvr_name = self.dvr_table.item(curr_row, 0).text()
        dvr_data = self.config.get_dvr_by_name(self.selected_condo_id, dvr_name)
        if not dvr_data:
            return
            
        dialog = InputDialog("Editar DVR", self.get_dvr_fields(), self, initial_values=dvr_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            updated_data = {
                "nome": data["nome"],
                "ip": data["ip"],
                "onvif_port": int(data["onvif_port"]) if data["onvif_port"].isdigit() else 80,
                "user": data["user"],
                "password": data["password"]
            }
            # Se mudou o nome, remove o anterior e insere o novo
            if dvr_name != updated_data["nome"]:
                self.config.delete_dvr(self.selected_condo_id, dvr_name)
            self.config.add_dvr(self.selected_condo_id, updated_data)
            self.refresh_dvr_table()

    def delete_dvr(self):
        curr_row = self.dvr_table.currentRow()
        if curr_row < 0:
            return
            
        dvr_name = self.dvr_table.item(curr_row, 0).text()
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Excluir DVR '{dvr_name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config.delete_dvr(self.selected_condo_id, dvr_name)
            self.refresh_dvr_table()

    # --- CRUD Câmeras ---
    def get_camera_fields(self):
        # Busca DVRs disponíveis para popular o combo
        conds = self.config.get_condominios()
        dvrs_list = ["Direta (Sem DVR)"]
        for cond in conds:
            if cond.get("id") == self.selected_condo_id:
                for d in cond.get("dvrs", []):
                    dvrs_list.append(d.get("nome"))
                    
        return [
            ("nome", "text", "Nome da Câmera:"),
            ("dvr", "combo", (dvrs_list, "Selecionar DVR:")),
            ("canal", "text", "Canal DVR (1-64):"),
            ("stream_tipo", "combo", (["sub", "main"], "Tipo de Fluxo:")),
            ("url", "text", "URL Direta (RTSP/HTTP se sem DVR):")
        ]

    def add_camera(self):
        dialog = InputDialog("Nova Câmera", self.get_camera_fields(), self, initial_values={"canal": "1"})
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data["nome"]:
                cam_data = {
                    "nome": data["nome"],
                    "stream_tipo": data["stream_tipo"]
                }
                
                if data["dvr"] != "Direta (Sem DVR)":
                    cam_data["dvr"] = data["dvr"]
                    cam_data["canal"] = int(data["canal"]) if data["canal"].isdigit() else 1
                else:
                    cam_data["url"] = data["url"]
                    
                self.config.add_camera(self.selected_condo_id, cam_data)
                self.refresh_camera_table()

    def edit_camera(self):
        curr_row = self.cam_table.currentRow()
        if curr_row < 0:
            return
            
        cam_name = self.cam_table.item(curr_row, 0).text()
        # Encontra os dados atuais
        curr_cam_data = None
        for cond in self.config.get_condominios():
            if cond.get("id") == self.selected_condo_id:
                for cam in cond.get("cameras", []):
                    if cam.get("nome") == cam_name:
                        curr_cam_data = cam
                        break
                        
        if not curr_cam_data:
            return
            
        initials = {
            "nome": curr_cam_data.get("nome", ""),
            "dvr": curr_cam_data.get("dvr", "Direta (Sem DVR)"),
            "canal": str(curr_cam_data.get("canal", "1")),
            "stream_tipo": curr_cam_data.get("stream_tipo", "sub"),
            "url": curr_cam_data.get("url", "")
        }
        
        dialog = InputDialog("Editar Câmera", self.get_camera_fields(), self, initial_values=initials)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            updated_data = {
                "nome": data["nome"],
                "stream_tipo": data["stream_tipo"]
            }
            
            if data["dvr"] != "Direta (Sem DVR)":
                updated_data["dvr"] = data["dvr"]
                updated_data["canal"] = int(data["canal"]) if data["canal"].isdigit() else 1
            else:
                updated_data["url"] = data["url"]
                
            if cam_name != updated_data["nome"]:
                self.config.delete_camera(self.selected_condo_id, cam_name)
                
            self.config.add_camera(self.selected_condo_id, updated_data)
            self.refresh_camera_table()

    def delete_camera(self):
        curr_row = self.cam_table.currentRow()
        if curr_row < 0:
            return
            
        cam_name = self.cam_table.item(curr_row, 0).text()
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Excluir câmera '{cam_name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config.delete_camera(self.selected_condo_id, cam_name)
            self.refresh_camera_table()

    def scan_network(self):
        """Busca dispositivos ONVIF na rede local e exibe para importação."""
        from src.onvif_service import discover_onvif_devices
        
        # Alerta visual rápido
        QMessageBox.information(
            self, "Varredura de Rede",
            "Iniciando busca por dispositivos ONVIF na sua rede local.\n"
            "Esta varredura pode levar cerca de 2 segundos. Clique em OK para começar.",
            QMessageBox.Ok
        )
        
        urls = discover_onvif_devices()
        
        if not urls:
            QMessageBox.warning(
                self, "Nenhum Dispositivo Encontrado",
                "Nenhum dispositivo ONVIF (câmera IP ou DVR) respondeu à varredura multicast.\n"
                "Verifique se os dispositivos estão ligados, na mesma sub-rede e com o ONVIF ativado.",
                QMessageBox.Ok
            )
            return
            
        # Extrai IPs das URLs localizadas
        import urllib.parse
        ips = []
        for url in urls:
            parsed = urllib.parse.urlparse(url)
            host = parsed.netloc if parsed.netloc else parsed.path.split('/')[0]
            if host not in ips:
                ips.append(host)
                
        # Mostra um diálogo para seleção
        options_list = [f"IP: {ip} (Endereço: {url})" for ip, url in zip(ips, urls)]
        
        fields = [("dvr_select", "combo", (options_list, "Dispositivos Localizados:"))]
        dialog = InputDialog("Dispositivos ONVIF Encontrados", fields, self)
        
        if dialog.exec() == QDialog.Accepted:
            selected_str = dialog.get_data().get("dvr_select")
            if selected_str:
                # Extrai o host/IP
                # Formato: "IP: 192.168.1.100:80 (Endereço: ...)"
                try:
                    ip_part = selected_str.split(" (")[0].replace("IP: ", "")
                    host_ip = ip_part.split(":")[0]
                    port_part = ip_part.split(":")[1] if ":" in ip_part else "80"
                    
                    # Abre o formulário de cadastro pré-preenchido com o IP
                    dvr_dialog = InputDialog(
                        "Adicionar DVR Localizado", 
                        self.get_dvr_fields(), 
                        self, 
                        initial_values={"ip": host_ip, "onvif_port": port_part, "user": "admin"}
                    )
                    if dvr_dialog.exec() == QDialog.Accepted:
                        data = dvr_dialog.get_data()
                        if data["nome"] and data["ip"]:
                            dvr_data = {
                                "nome": data["nome"],
                                "ip": data["ip"],
                                "onvif_port": int(data["onvif_port"]) if data["onvif_port"].isdigit() else 80,
                                "user": data["user"],
                                "password": data["password"]
                            }
                            self.config.add_dvr(self.selected_condo_id, dvr_data)
                            self.refresh_dvr_table()
                except Exception as e:
                    print(f"Erro ao importar dispositivo localizado: {e}")
