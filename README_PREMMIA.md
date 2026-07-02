# Automação Premmia

Esta automação fica na aba `Premmia` do sistema e gera uma planilha `.xlsx`
formatada para cada planilha bruta selecionada.

## Como usar

1. Abra o sistema.
2. Entre na aba `Premmia`.
3. Escolha a `Pasta de Saída`.
4. Clique em `+ Adicionar arquivo(s)` e selecione uma ou mais planilhas brutas.
5. Clique em `Executar`.

Cada arquivo bruto gera um arquivo `.xlsx` com o mesmo nome na pasta de saída.
Se já existir um arquivo com esse nome, ele será substituído.

## Estrutura esperada

- Brutos de exemplo: `dados/automacoesToDo/brutos/`
- Modelo final interno: `dados/automacoesToDo/modeloFinal/`
- Saída padrão: `dados/automacoesToDo/formatados/`

## Debug

Se algum arquivo falhar, veja a área de log da aba `Premmia`. As causas mais
comuns são: aba obrigatória ausente, cabeçalhos diferentes do esperado ou
arquivo aberto no Excel durante a gravação.
