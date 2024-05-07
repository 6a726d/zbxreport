import json, requests, time
from django.contrib import messages
from django.shortcuts import redirect

class ZbxAPI:
    
    def get_zabbix_token(apiurl, apiusr, apipass, request):
        url = apiurl
        headers = {'Content-Type': 'application/json-rpc'}
        data = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "username": apiusr,
                "password": apipass
            },
            "id": 1,
            "auth": None
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and result['result']:
                return result['result']
            elif 'error' in result:
                messages.error(request, "Usuário/senha incorretos ou conta bloqueada")
        else:
            messages.error(request, f"Erro na requisição: {response.status_code}")

class ZbxHostGroup:

    def get_host_groups(apiurl, token, request):
        url = apiurl
        headers = {'Content-Type': 'application/json-rpc'}
        data = {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": ["groupid", "name"]
            },
            "id": 2,
            "auth": token
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and result['result']:
                messages.success(request, 'Lista de Hostgroups atualizada!')
                return result['result']
            elif 'error' in result:
                messages.error(request, "Erro ao obter grupos de hosts: " + result['error'].get('data', ''))
        else:
            messages.error(request, f"Erro na requisição: {response.status_code}")
        
class ZbxHost:
        
    def get_hosts(apiurl, token, request):
        url = apiurl
        headers = {'Content-Type': 'application/json-rpc'}
        data = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid", "name"], 
                "selectGroups": ["groupid", "name"],
            },
            "id": 2,
            "auth": token
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and result['result']:
                messages.success(request, 'Lista de Hosts atualizada!')
                return result['result']
            elif 'error' in result:
                messages.error(request, "Erro ao obter hosts e grupos: " + result['error'].get('data', ''))
        else:
            messages.error(request, f"Erro na requisição: {response.status_code}")

class ZbxItens:

    def get_itens(apiurl, token, request):
        url = apiurl
        headers = {'Content-Type': 'application/json-rpc'}
        data = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["itemid", "name"],
                "sortfield": "name"  
            },
            "id": 3,
            "auth": token  # Usa o token de autenticação obtido anteriormente
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and result['result']:
                messages.success(request, 'Lista de Itens atualizada!')
                return result['result']
            elif 'error' in result:
                messages.error(request, "Erro ao obter itens: " + result['error'].get('data', ''))
        else:
            messages.error(request, f"Erro na requisição: {response.status_code}")
        
    def get_itens_hosts(apiurl, token, request):
        url = apiurl
        headers = {'Content-Type': 'application/json-rpc'}
        data = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["itemid", "name"],
                "selectHosts": ["hostid"],  # Solicita também o ID do host
                "sortfield": "name"
            },
            "id": 4,  # Incrementa o ID da requisição
            "auth": token
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and result['result']:
                # Processa os resultados para incluir o ID do host
                items_with_hosts = []
                for item in result['result']:
                    if item['hosts']:  # Verifica se existe informações do host associado
                        host_id = item['hosts'][0]['hostid']  # Assume o primeiro host, se houver múltiplos
                        items_with_hosts.append({
                            'itemid': item['itemid'],
                            'name': item['name'],
                            'hostid': host_id
                        })
                messages.success(request, 'Integração Itens/Hosts atualizada!')
                return items_with_hosts
            elif 'error' in result:
                messages.error(request, "Erro ao obter itens e hosts: " + result['error'].get('data', ''))
        else:
            messages.error(request, f"Erro na requisição: {response.status_code}")
        
        
class ZbxHistory:

    def get_item_types(apiurl, token, itemids, request):
        url = apiurl
        headers = {'Content-Type': 'application/json-rpc'}
        data = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "itemids": itemids,
                "output": ["itemid", "value_type"]
            },
            "id": 1,
            "auth": token
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and result['result']:
                # Retorna uma lista de dicionários com itemid e o seu tipo
                return [{"itemid": item['itemid'], "type": item['value_type']} for item in result['result']]
            elif 'error' in result:
                messages.error(request, "Erro ao obter tipos dos itens: " + result['error'].get('data', ''))
        else:
            messages.error(request, f"Erro na requisição: {response.status_code}")

    def get_item_history(apiurl, token, itemids, start_date, end_date, request):
        items_with_types = ZbxHistory.get_item_types(apiurl, token, itemids, request)

        url = apiurl
        headers = {'Content-Type': 'application/json-rpc'}
        format_str = "%Y-%m-%dT%H:%M"  # Formato da data

        start_timestamp = int(time.mktime(time.strptime(start_date, format_str)))
        end_timestamp = int(time.mktime(time.strptime(end_date, format_str)))

        all_results = []

        for item in items_with_types:
            data = {
                "jsonrpc": "2.0",
                "method": "history.get",
                "params": {
                    "itemids": item["itemid"],
                    "history": item["type"],  # Usa o tipo correto para cada item
                    "time_from": start_timestamp,
                    "time_till": end_timestamp,
                    "output": "extend",
                    "sortfield": "clock",
                    "sortorder": "ASC"
                },
                "id": 5,
                "auth": token
            }

            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                result = response.json()
                if 'result' in result and result['result']:
                    all_results.extend(result['result'])  # Adiciona os resultados na lista geral
                elif 'error' in result:
                    messages.error(request, f"Erro ao obter histórico: " + result['error'].get('data', ''))
            else:
                messages.error(request, f"Erro na requisição: {response.status_code}")

        return all_results