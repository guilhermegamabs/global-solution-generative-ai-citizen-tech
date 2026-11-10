class ApiFailure(Exception):
    codigoStatus = 500
    mensagemUsuario = "Algo deu errado. Tente novamente em instantes."
    codigoErro = None


class ProviderUnavailableError(ApiFailure):
    codigoStatus = 503
    mensagemUsuario = "O serviço de análise está indisponível no momento. Tente novamente em alguns minutos."


class ProviderTimeoutError(ApiFailure):
    codigoStatus = 504
    mensagemUsuario = "A análise demorou mais do que o esperado. Tente novamente em instantes."


class InvalidModelResponseError(ApiFailure):
    codigoStatus = 502
    mensagemUsuario = "Não conseguimos montar a orientação desta vez. Tente novamente."


class RecordNotFoundError(ApiFailure):
    codigoStatus = 404
    mensagemUsuario = "Não encontramos essa solicitação. Faça uma nova análise."


class CepNotFoundError(ApiFailure):
    codigoStatus = 404
    mensagemUsuario = "Não encontramos esse CEP. Confira os números e tente de novo."


class LocationUnavailableError(ApiFailure):
    codigoStatus = 503
    mensagemUsuario = "Não conseguimos localizar esse endereço agora. Tente novamente em instantes."


class UnitsUnavailableError(ApiFailure):
    codigoStatus = 503
    mensagemUsuario = "A lista de UPAs está indisponível no momento. Tente novamente em alguns minutos."


class NoUnitsFoundError(ApiFailure):
    codigoStatus = 404
    mensagemUsuario = "Não encontramos UPAs cadastradas na sua cidade. Procure a unidade de saúde mais próxima."


class InvalidReviewError(ApiFailure):
    codigoStatus = 422
    mensagemUsuario = "Para corrigir a urgência, escolha qual nível você considera correto."


class AuthRequiredError(ApiFailure):
    codigoStatus = 401
    mensagemUsuario = "Sua sessão acabou. Entre na sua conta para continuar."
    codigoErro = "sessionExpired"


class InvalidCredentialsError(ApiFailure):
    codigoStatus = 401
    mensagemUsuario = "E-mail ou senha incorretos."


class EmailNotVerifiedError(ApiFailure):
    codigoStatus = 403
    mensagemUsuario = "Confirme seu e-mail para entrar. Enviamos um código para você."
    codigoErro = "emailNotVerified"


class EmailAlreadyRegisteredError(ApiFailure):
    codigoStatus = 409
    mensagemUsuario = "Este e-mail já tem uma conta. Entre com a sua senha."


class InvalidCodeError(ApiFailure):
    codigoStatus = 400
    mensagemUsuario = "Código incorreto ou vencido. Confira os números ou peça um novo código."


class TooManyAttemptsError(ApiFailure):
    codigoStatus = 429
    mensagemUsuario = "Muitas tentativas erradas. Peça um novo código."


class ResendTooSoonError(ApiFailure):
    codigoStatus = 429
    mensagemUsuario = "Aguarde um minuto para pedir um novo código."


class TooManyLoginAttemptsError(ApiFailure):
    codigoStatus = 429
    mensagemUsuario = "Muitas tentativas de entrada. Aguarde alguns minutos e tente de novo."


class EmailUnavailableError(ApiFailure):
    codigoStatus = 503
    mensagemUsuario = (
        "Não conseguimos enviar o código para o seu e-mail agora. "
        "Confira se o endereço está certo e tente de novo em alguns minutos."
    )
