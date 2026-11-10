from app.errors import CepNotFoundError, LocationUnavailableError
from app.pipelines.unitsPipeline import calcularDistanciaKm
from app.providers.cnesProvider import normalizarUnidade
from app.providers.geocodeProvider import escolherPonto, montarConsultas, simplificarNome
from conftest import sobrescreverFontes

enderecoSp = {"ibge": "3550308", "localidade": "São Paulo", "uf": "SP", "bairro": "Bela Vista", "logradouro": "Avenida Paulista"}

unidadesFalsas = [
    {"name": "UPA Longe", "address": "Rua A, 1", "neighborhood": "X", "phone": None, "latitude": -23.60, "longitude": -46.40, "open24h": True},
    {"name": "UPA Perto", "address": "Rua B, 2", "neighborhood": "Y", "phone": "(11) 1111-1111", "latitude": -23.562, "longitude": -46.656, "open24h": True},
    {"name": "UPA Meio", "address": "Rua C, 3", "neighborhood": "Z", "phone": None, "latitude": -23.52, "longitude": -46.60, "open24h": False},
]


def montarFontes(**trocas):
    fontes = {
        "buscarCep": lambda cep: enderecoSp,
        "geocodificar": lambda endereco: (-23.5614, -46.6559, False),
        "listarUnidades": lambda codigo: unidadesFalsas,
        "coordenadasPorCep": lambda cep: None,
        "pontoPorNome": lambda nome, cidade, estado: None,
    }
    fontes.update(trocas)
    return fontes


def levantar(erro):
    def acao(*argumentos):
        raise erro()

    return acao


def testeOrdenaPorDistanciaERespeitaLimite(cliente):
    sobrescreverFontes(montarFontes())
    resposta = cliente.post("/units/nearby", json={"cep": "01310-100", "limit": 2})
    corpo = resposta.json()
    assert resposta.status_code == 200
    assert [unidade["name"] for unidade in corpo["units"]] == ["UPA Perto", "UPA Meio"]
    assert corpo["origin"]["city"] == "São Paulo"


def testeOrigemAproximadaQuandoSoAchaACidade(cliente):
    sobrescreverFontes(montarFontes(geocodificar=lambda endereco: (-23.55, -46.63, True)))
    corpo = cliente.post("/units/nearby", json={"cep": "01310-100"}).json()
    assert corpo["origin"]["approximate"] is True


def testeConsultasSempreRestringemACidade():
    consultas = montarConsultas({"logradouro": "Rua Bernardo Taveira Júnior", "bairro": "Parque Primavera", "localidade": "São Paulo", "uf": "SP"})
    assert all(parametros["city"] == "São Paulo" and parametros["state"] == "SP" for parametros, aproximado in consultas)
    assert [aproximado for parametros, aproximado in consultas] == [False, True]
    assert "q" not in consultas[0][0]


def testeSemLogradouroUsaSoACidade():
    consultas = montarConsultas({"logradouro": "", "localidade": "Santos", "uf": "SP"})
    assert len(consultas) == 1
    assert consultas[0][1] is True


def testeMarcaPosicaoIncertaQuandoCepDivergeDoCnes(cliente):
    unidadesComCep = [{**unidade, "cep": f"0000000{posicao}"} for posicao, unidade in enumerate(unidadesFalsas)]
    sobrescreverFontes(
        montarFontes(
            listarUnidades=lambda codigo: unidadesComCep,
            coordenadasPorCep=lambda cep: (-23.70, -46.70) if cep.endswith("1") else (-23.562, -46.656),
        )
    )
    unidades = cliente.post("/units/nearby", json={"cep": "01310-100", "limit": 3}).json()["units"]
    marcas = {unidade["name"]: unidade["positionUncertain"] for unidade in unidades}
    assert marcas["UPA Perto"] is True


def testeNaoMarcaQuandoCoordenadasDoCepConcordam(cliente):
    unidadesComCep = [{**unidade, "cep": "04447021"} for unidade in unidadesFalsas]
    sobrescreverFontes(
        montarFontes(
            listarUnidades=lambda codigo: unidadesComCep,
            coordenadasPorCep=lambda cep: (-23.562, -46.656),
        )
    )
    unidades = cliente.post("/units/nearby", json={"cep": "01310-100", "limit": 1}).json()["units"]
    assert unidades[0]["name"] == "UPA Perto"
    assert unidades[0]["positionUncertain"] is False


def testeSemCoordenadasDoCepNaoMarcaIncerteza(cliente):
    sobrescreverFontes(montarFontes())
    unidades = cliente.post("/units/nearby", json={"cep": "01310-100"}).json()["units"]
    assert all(unidade["positionUncertain"] is False for unidade in unidades)


def testeRefinaPosicaoIncertaEReordenaALista(cliente):
    cadastradas = [
        {"name": "UPA Cadastro Errado", "address": "Rua A, 1", "neighborhood": "X", "phone": None, "latitude": -23.5614, "longitude": -46.6559, "open24h": True, "cep": "04447021"},
        {"name": "UPA Meio", "address": "Rua B, 2", "neighborhood": "Y", "phone": None, "latitude": -23.5614, "longitude": -46.6259, "open24h": True, "cep": "04447022"},
    ]
    sobrescreverFontes(
        montarFontes(
            listarUnidades=lambda codigo: cadastradas,
            coordenadasPorCep=lambda cep: (-23.60, -46.60) if cep.endswith("1") else None,
            pontoPorNome=lambda nome, cidade, estado: (-23.5614, -46.6119) if nome == "UPA Cadastro Errado" else None,
        )
    )
    unidades = cliente.post("/units/nearby", json={"cep": "01310-100", "limit": 2}).json()["units"]
    assert [unidade["name"] for unidade in unidades] == ["UPA Meio", "UPA Cadastro Errado"]
    refinada = unidades[1]
    assert refinada["positionUncertain"] is False
    assert refinada["distanceKm"] > 4


def testeIgnoraPontoMuitoLongeDoCadastro(cliente):
    unidadesComCep = [{**unidade, "cep": "04447021"} for unidade in unidadesFalsas]
    sobrescreverFontes(
        montarFontes(
            listarUnidades=lambda codigo: unidadesComCep,
            coordenadasPorCep=lambda cep: (-23.70, -46.70),
            pontoPorNome=lambda nome, cidade, estado: (-22.00, -51.00),
        )
    )
    unidades = cliente.post("/units/nearby", json={"cep": "01310-100", "limit": 3}).json()["units"]
    assert all(unidade["positionUncertain"] for unidade in unidades)


def testeSimplificaNomeCortandoNoHonorifico():
    assert simplificarNome("UPA PEDREIRA DR CESAR ANTUNES DA ROCHA") == "Upa Pedreira"
    assert simplificarNome("UPA VERGUEIRO") == "Upa Vergueiro"


def testeEscolhePontoSoDeSaudeNaCidade():
    achados = [
        {"class": "highway", "display_name": "Rua Pedreira, São Paulo", "lat": "-23.1", "lon": "-46.1"},
        {"class": "amenity", "display_name": "UPA Pedreira, Presidente Prudente", "lat": "-22.1", "lon": "-51.3"},
        {"class": "amenity", "display_name": "UPA Pedreira, Pedreira, São Paulo", "lat": "-23.695", "lon": "-46.676"},
    ]
    assert escolherPonto(achados, "São Paulo") == (-23.695, -46.676)
    assert escolherPonto(achados[:2], "São Paulo") is None


def testeCodigoDoMunicipioTemSeisDigitos(cliente):
    recebido = []
    sobrescreverFontes(montarFontes(listarUnidades=lambda codigo: recebido.append(codigo) or unidadesFalsas))
    cliente.post("/units/nearby", json={"cep": "01310100"})
    assert recebido == ["355030"]


def testeCepInvalidoERejeitado(cliente):
    sobrescreverFontes(montarFontes())
    assert cliente.post("/units/nearby", json={"cep": "123"}).status_code == 422
    assert cliente.post("/units/nearby", json={"cep": "abcde-fgh"}).status_code == 422


def testeCepNaoEncontrado(cliente):
    sobrescreverFontes(montarFontes(buscarCep=levantar(CepNotFoundError)))
    resposta = cliente.post("/units/nearby", json={"cep": "99999-999"})
    assert resposta.status_code == 404
    assert "CEP" in resposta.json()["message"]


def testeGeocodificadorForaDoAr(cliente):
    sobrescreverFontes(montarFontes(geocodificar=levantar(LocationUnavailableError)))
    resposta = cliente.post("/units/nearby", json={"cep": "01310-100"})
    assert resposta.status_code == 503


def testeSemUpasNoMunicipio(cliente):
    sobrescreverFontes(montarFontes(listarUnidades=lambda codigo: []))
    resposta = cliente.post("/units/nearby", json={"cep": "01310-100"})
    assert resposta.status_code == 404


def testeDistanciaEntreSaoPauloERio():
    distancia = calcularDistanciaKm(-23.5505, -46.6333, -22.9068, -43.1729)
    assert 350 < distancia < 370


def testeNormalizaUnidadeValida():
    unidade = normalizarUnidade(
        {
            "nome_fantasia": "UPA CENTRO",
            "endereco_estabelecimento": "RUA MIGUEL NOVAIS",
            "numero_estabelecimento": "113",
            "bairro_estabelecimento": "VILA PARANAGUA",
            "numero_telefone_estabelecimento": "(11)5283-8171",
            "latitude_estabelecimento_decimo_grau": -23.49,
            "longitude_estabelecimento_decimo_grau": -46.47,
            "descricao_turno_atendimento": "ATENDIMENTO CONTINUO DE 24 HORAS/DIA",
            "codigo_motivo_desabilitacao_estabelecimento": None,
            "estabelecimento_faz_atendimento_ambulatorial_sus": "SIM",
        }
    )
    assert unidade["address"] == "Rua Miguel Novais, 113"
    assert unidade["open24h"] is True


def testeIgnoraUnidadeSemCoordenadaOuDesabilitada():
    base = {
        "nome_fantasia": "UPA",
        "latitude_estabelecimento_decimo_grau": -23.4,
        "longitude_estabelecimento_decimo_grau": -46.4,
        "estabelecimento_faz_atendimento_ambulatorial_sus": "SIM",
    }
    assert normalizarUnidade({**base, "latitude_estabelecimento_decimo_grau": None}) is None
    assert normalizarUnidade({**base, "codigo_motivo_desabilitacao_estabelecimento": "12"}) is None


def testeFiltraPrivadaMasMantemUpaSemFlagSus():
    base = {
        "latitude_estabelecimento_decimo_grau": -23.4,
        "longitude_estabelecimento_decimo_grau": -46.4,
        "estabelecimento_faz_atendimento_ambulatorial_sus": "NAO",
    }
    assert normalizarUnidade({**base, "nome_fantasia": "NOTRE DAME INTERMEDICA"}) is None
    assert normalizarUnidade({**base, "nome_fantasia": "UPA VILA PRUDENTE"}) is not None
