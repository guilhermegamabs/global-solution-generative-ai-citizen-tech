from app.schemas.triageSchemas import AgeRange, Duration, WarningSign

rotulosFaixaEtaria = {
    AgeRange.child: "Criança (0 a 12 anos)",
    AgeRange.teen: "Adolescente (13 a 17 anos)",
    AgeRange.adult: "Adulto (18 a 59 anos)",
    AgeRange.senior: "Idoso (60 anos ou mais)",
}

rotulosDuracao = {
    Duration.lessThanDay: "Menos de 1 dia",
    Duration.oneToThreeDays: "De 1 a 3 dias",
    Duration.fourToSevenDays: "De 4 a 7 dias",
    Duration.moreThanWeek: "Mais de 1 semana",
}

rotulosSinaisAlerta = {
    WarningSign.chestPain: "Dor forte no peito",
    WarningSign.breathingDifficulty: "Dificuldade para respirar",
    WarningSign.lossOfConsciousness: "Desmaio ou perda de consciência",
    WarningSign.severeBleeding: "Sangramento que não para",
    WarningSign.confusion: "Confusão mental ou fala enrolada",
    WarningSign.strokeSigns: "Boca torta, fraqueza em um lado do corpo",
    WarningSign.highFever: "Febre alta (acima de 39 °C)",
}

sinaisEmergencia = {
    WarningSign.chestPain,
    WarningSign.breathingDifficulty,
    WarningSign.lossOfConsciousness,
    WarningSign.severeBleeding,
    WarningSign.confusion,
    WarningSign.strokeSigns,
}
