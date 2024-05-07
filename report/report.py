from base.models import TBLayout, TBHost, TBItens, TBMiddleItem, TBMiddleLayout, TBHostGroup
from django.db.models.query import QuerySet
import json, os, time, base64
from django.http import FileResponse, HttpResponseNotFound, HttpResponse
from django.conf import settings
from weasyprint import HTML, CSS
from pyppeteer import launch
from reportlab.lib.pagesizes import letter
import matplotlib.pyplot as plt
from datetime import datetime, timezone
import numpy as np

class CreateReport:

    def createGraph(history, layoutpk, user_id):
        itemlist = [i.mdlitemname for i in TBMiddleLayout.objects.filter(mdlid__pk = layoutpk)]
        zbxitemlist = [str(i.mdiitemid) for i in TBMiddleItem.objects.filter(mdiitemname__in = itemlist)]

        data_by_itemid = {}
        for entry in history:
            itemid = entry['itemid']

            if itemid not in zbxitemlist:
                continue

            timestamp = datetime.fromtimestamp(int(entry['clock']), tz=timezone.utc)
            readable_date = timestamp.strftime('%d/%m/%y - %H:%M')
            try:
                value = float(entry['value'])
            except ValueError:
                continue
            
            if itemid not in data_by_itemid:
                data_by_itemid[itemid] = []
            data_by_itemid[itemid].append((readable_date, value))

        plt.rc('axes', edgecolor='#888888')  # Cor da borda dos eixos
        plt.rc('axes', facecolor='#F5F5F5')  # Cor de fundo dos eixos
        plt.rc('figure', facecolor='white')  # Cor de fundo da figura
        plt.rc('xtick', color='#666666')  # Cor dos ticks no eixo x
        plt.rc('ytick', color='#666666')  # Cor dos ticks no eixo y
        plt.rc('grid', color='lightgray')  # Cor da grade
        
        # Gerando e salvando os gráficos
        for itemid, data in data_by_itemid.items():
            data.sort(key=lambda x: x[0])  # Ordenando pela data, se necessário
            dates, values = zip(*data)

            plt.figure(figsize=(10, 6))

            ax = plt.gca()

            cor_da_borda = '#000000'
            for spine in ax.spines.values():
                spine.set_edgecolor(cor_da_borda)

            plt.plot(dates, values, linestyle='-', linewidth=1, color='dodgerblue')
            
            # Determinar quais datas devem ser exibidas na legenda do eixo x
            if len(dates) > 10:
                indices_para_rotulos = np.round(np.linspace(0, len(dates) - 1, 10)).astype(int)
                datas_para_rotulos = [dates[i] for i in indices_para_rotulos]
                plt.xticks(indices_para_rotulos, datas_para_rotulos, rotation=45)
            else:
                plt.xticks(rotation=45)
            
            plt.grid(True, which='both')
            plt.tight_layout()
            
            plt.title('')
            plt.xlabel('')
            plt.ylabel('')
            
            # Salvando o gráfico
            report_path = os.path.join(settings.MEDIA_ROOT, 'report', f'{user_id}_{itemid}.png')
            os.makedirs(os.path.dirname(report_path), exist_ok=True)  # Garantindo que o diretório exista
            plt.savefig(report_path)
            plt.close()


    def get_logo_base64(user_id):
        image_path = os.path.join(settings.MEDIA_ROOT, 'logo', f'{user_id}.png')
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def get_graph_base64(user_id, itemid):
        try:
            # Constrói o caminho do arquivo de imagem
            image_path = os.path.join(settings.MEDIA_ROOT, 'report', f'{user_id}_{itemid}.png')
            # Tenta abrir o arquivo de imagem
            with open(image_path, 'rb') as image_file:
                # Se conseguiu abrir, retorna a imagem codificada em base64
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            # Se o arquivo não for encontrado, retorna None para indicar isso
            return None

    def create_report(mditem_list, layoutpk, hostgroup, datefrom, dateto, user_id):
        layout = TBLayout.objects.get(pk=layoutpk)
        group = TBHostGroup.objects.get(pk=hostgroup)
        datefrom = datetime.strptime(datefrom, "%Y-%m-%dT%H:%M")
        dateto = datetime.strptime(dateto, "%Y-%m-%dT%H:%M")

        datefromdt = datefrom.strftime("%d/%m/%y")
        datefromhr = datefrom.strftime("%H:%M")
        datetodt = dateto.strftime("%d/%m/%y")
        datetohr = dateto.strftime("%H:%M")

        mdl_item_ids = TBMiddleLayout.objects.filter(mdlid=layoutpk).values_list('mdlitemname_id', flat=True)
        mdl_item_names = TBItens.objects.filter(id__in=mdl_item_ids).values_list('itemname', flat=True)

        items_by_host = {}
        for mditem in mditem_list:
            hostname = mditem.mdihostid.hostname
            if hostname not in items_by_host:
                items_by_host[hostname] = []
            if mditem.mdiitemname.itemname in mdl_item_names:
                items_by_host[hostname].append(mditem)

        css_styles = """
        <style>
            .user-image { width: 200px; height: auto; }
            .logo-container { display: flex; justify-content: center; }
            .head-container { margin-bottom: 30px; }
            body { font-family: 'Arial', sans-serif; margin: 20px; color: #333; }
            h1, h2 { color: black; }
            h3 { color: black; margin-top: 20px; }
            div.host { margin-bottom: 20px; }
            p { margin: 5px 0; text-align: justify; }
            .chart-container { width: 100%; height: auto; margin: 0 auto; align-items: center; justify-content: center; display: flex; margin-bottom: 50px; margin-top: 30px; }
            canvas { display: block; width: 100%; height: 100%; }
            .container { padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .graph-image { width: 630px; height: auto; }
            .hostname { margin-botton: 40px; align-items: center; justify-content: center; display: flex; }
            .itemname { margin-botton: 15px; }
            .dsc { font-size: 12px; }
            .empresa { align-items: center; justify-content: center; display: flex; color: black; }
        </style>
        """
        logo_base64 = CreateReport.get_logo_base64(user_id)
        html_content = f"""
        <html>
        <head>
            <title>Relatório: {layout.layoutname}</title>
            {css_styles}
        </head>
        <body>
            <div class="container">
                <div class="logo-container">
                    <img src="data:image/png;base64,{logo_base64}" alt="User Image" class="user-image">
                </div>
                <div class="head-container">
                    <div class="empresa">
                        <h3>{layout.layoutemp}</h3>
                    </div>
                    <p><strong>Relatório:</strong> {group.gpname} - {layout.layoutname}</p>
                    <p><strong>Período:</strong> De {datefromdt} às {datefromhr} até {datetodt} às {datetohr}.</p>
                    <p>{layout.layoutdsc}</p>
                </div>
        """

        for hostname, items in items_by_host.items():
            html_content += f"""
            <div class="host">
                <div class="hostname">
                    <h3>{hostname}</h3>
                </div>
            """
            if not items:  # Se não houver itens para o hostname
                html_content += f"""
                    <p><em>Sem itens atribuídos nesse layout</em></p>
                """
            else:
                for item in items:
                    graph_base64 = CreateReport.get_graph_base64(user_id, item.mdiitemid)
                    if graph_base64:
                        html_content += f"""
                            <div class="item">
                                <div class="itemname">
                                    <p><strong>Host:</strong> {hostname}</p>
                                </div>
                                <div class="itemname">
                                    <p><strong>Item:</strong> {item.mdiitemname.itemname}</p>
                                </div>
                                <div class="dsc">
                                    <p><strong>Descrição:</strong> {item.mdiitemname.itemdscreport}</p>
                                </div>
                                <div class="chart-container">
                                    <img src="data:image/png;base64,{graph_base64}" alt="Graph Image" class="graph-image">
                                </div>
                            </div>
                        """
                    else:
                        html_content += f"""
                            <div class="item">
                                <div class="itemname">
                                    <p><strong>Host:</strong> {hostname}</p>
                                </div>
                                <div class="itemname">
                                    <p><strong>Item:</strong> {item.mdiitemname.itemname}</p>
                                </div>
                                <div class="dsc">
                                <p><strong>Descrição:</strong> {item.mdiitemname.itemdscreport}</p>
                                </div>
                                <div class="chart-container">
                                    <p><em>Sem dados</em></p>
                                </div>
                            </div>
                        """
            html_content += "</div>"

        html_content += """
            </div>
        </body>
        </html>
        """

        return html_content
    
    def gerarPDF(request, html_content):
        # Certifique-se de definir MEDIA_ROOT no seu settings.py
        media_root = settings.MEDIA_ROOT
        report_dir = 'report'
        user_id = request.user.id
        filename = f'{user_id}.pdf'  # Modifica o nome do arquivo para incluir o timestamp
        file_path = os.path.join(media_root, report_dir, filename)
        
        # Cria o diretório se ele não existir
        if not os.path.exists(os.path.join(media_root, report_dir)):
            os.makedirs(os.path.join(media_root, report_dir))
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                return HttpResponseNotFound(f'Erro ao tentar excluir o arquivo existente: {e.strerror}')

        css = CSS(string='''
            @page { margin: 7mm; margin-top: 15mm; } 
        ''')
        
        # Gera o PDF e salva no caminho especificado
        HTML(string=html_content).write_pdf(file_path, stylesheets=[css])
        
        # Abre o arquivo para leitura em modo binário e cria uma resposta
        try:
            with open(file_path, 'rb') as pdf:
                response = FileResponse(pdf, as_attachment=True, filename=filename)
        except IOError:
            return HttpResponseNotFound('O arquivo não foi encontrado ou ocorreu um erro ao lê-lo.')
        
        # Retorna tanto a resposta quanto o nome do arquivo
        return filename
    
    def cleanGraphPNG(user_id):
        report_dir = os.path.join(settings.MEDIA_ROOT, 'report')
        
        # Verificando se o diretório existe
        if os.path.isdir(report_dir):
            # Listando todos os arquivos no diretório
            for filename in os.listdir(report_dir):
                # Construindo o caminho completo do arquivo
                file_path = os.path.join(report_dir, filename)
                # Verificando se o arquivo corresponde ao padrão de nomenclatura esperado
                if filename.startswith(f"{user_id}_") and filename.endswith(".png"):
                    # Removendo o arquivo
                    os.remove(file_path)
                    print(f"Removed: {file_path}")
        else:
            print("The report directory does not exist.")