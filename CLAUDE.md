# BlurImage, regras do projeto

Editor web local para aplicar blur em regiões retangulares de fotos. O usuário desenha, move, redimensiona e ajusta a intensidade de cada região; o arquivo exportado sai no mesmo formato, na mesma resolução e sem perda de qualidade fora das regiões.

A raiz é um único repositório git (`GustavoQ-Mateus/BlurImage`, público), com `backend/` e `frontend/`.

**Os critérios de aceite abaixo são dominantes.** Nenhuma mudança é dada como pronta, nem sobe para a `main`, se quebrar algum deles. Se o código ou uma decisão divergir dos critérios, valem os critérios e a divergência é corrigida antes de seguir.

## Critérios de aceite do produto
1. A imagem exportada tem a mesma largura, altura e formato da original.
2. JPEG: os coeficientes DCT de todos os blocos fora das regiões alinhadas à MCU são idênticos aos do original.
3. PNG e WebP: os pixels fora das regiões são idênticos aos do original.
4. HEIC: os blocos da grade que não tocam nenhuma região são idênticos aos do original; nos blocos tocados, os pixels fora das regiões ficam visualmente iguais (PSNR acima de 40 dB).
5. EXIF, perfil ICC (e, no PNG, os chunks de texto) continuam presentes e iguais, exceto a miniatura.
6. Nenhuma versão da área borrada sobrevive no arquivo: miniaturas (EXIF e HEIC) e imagens auxiliares do HEIC (mapa de ganho HDR, profundidade, transparência) recebem o mesmo blur, e os dados originais dos blocos trocados são removidos.
7. Uma região desenhada numa foto com orientação EXIF (ou `irot`/`imir` no HEIC) cai no lugar certo.

Cada critério tem teste automatizado no backend. Formato novo só entra com testes que cubram todos.

## Decisões de arquitetura
Respeite estas decisões. Mudar alguma exige discussão com o usuário antes do código.
- O navegador só edita e mostra prévia. O arquivo final é sempre gerado no backend, porque `canvas.toBlob()` recodifica a imagem e descarta metadados.
- JPEG nunca é recodificado inteiro: só os blocos que tocam as regiões são codificados de novo, com as tabelas de quantização e o subsampling originais, e inseridos com `jpegtran -drop`.
- WebP lossy é exportado em WebP lossless, para não somar perda.
- HEIC nunca é recodificado inteiro: fotos de celular são grades de blocos HEVC (512x512) e só os blocos que tocam as regiões são recodificados (qualidade 92, com a matriz de cor do original), editando a estrutura ISOBMFF em `app/heif/`. HEIC de imagem única é recodificado inteiro. HEIC com mais de 8 bits ou com `clap` é recusado.
- O navegador não exibe HEIC: o frontend mostra a prévia em JPEG gerada por `POST /api/preview`, já orientada.
- Miniaturas embutidas são refeitas com o blur aplicado, no mesmo tamanho em bytes no caso do EXIF.
- As regiões viajam em coordenadas da imagem orientada (como o navegador exibe); o backend converte para os pixels gravados.
- Backend sem estado e sem banco: `POST /api/blur` e `POST /api/preview`. O original nunca é sobrescrito.
- Uma única abstração de variação: o `Protocol` `Codec`, registrado por formato em `build_codecs`. Formato novo é uma classe nova.

Só implemente o que foi pedido; escopo novo é combinado antes de virar código. Se o pedido for ambíguo ou contradizer o código, pergunte antes de implementar.

## Estrutura
| Pasta | Stack | Papel |
|---|---|---|
| `backend` | Python 3.12, FastAPI, Pillow, pillow-heif, jpegtran (libjpeg-turbo), pytest | Processamento da imagem |
| `frontend` | React, Vite, TypeScript, react-konva, Vitest | Editor e prévia |

O `jpegtran` vem do libjpeg-turbo. No Windows fica em `C:\libjpeg-turbo64\bin\jpegtran.exe`; o backend procura na variável `JPEGTRAN` e depois no `PATH`.

## Código
- Simplicidade proporcional ao problema. Aplique KISS e YAGNI. Não adicione camadas de abstração, padrões de projeto, generalizações ou configurações que o pedido não exige. Resolva o problema atual, nunca o hipotético.
- Sem código documentado. Não escreva comentários explicativos nem docstrings. O código se explica por nomes claros de variáveis, funções e tipos. Comentário só em caso raro e genuinamente não óbvio, e curto.
- Idiomático por stack: TypeScript no front, Python no back. Siga o estilo já presente em cada pasta.
- Nada de dependência nova sem necessidade real.
- Nunca use travessão em nada gerado.
- Não alinhe colunas com espaços extras (atribuições, listas, dicionários). Um espaço só entre os elementos.
- Mudança de comportamento vem com teste, no padrão dos testes que já existem.
- Não altere o contrato de `POST /api/blur` e `POST /api/preview` sem pedido.
- Não altere o `README.md` sem pedido explícito, mesmo que fique desatualizado; avise em vez de editar.

## Estrutura de código
Princípios: Clean Code, SOLID, KISS e YAGNI, sempre na medida do pedido.

Geral
- Sem linha em branco entre declarações do mesmo tipo em sequência (propriedades, campos, parâmetros, imports). Linha em branco só separa blocos diferentes.
- Ordem dos membros: constantes, campos, construtor, propriedades, métodos públicos, métodos privados.
- Linha até ~120 colunas; passou disso, um argumento por linha.
- Retorno antecipado (guard clause) em vez de `if` aninhado; no máximo dois níveis de aninhamento.
- Funções curtas, uma responsabilidade. Trecho que pediria comentário vira função com nome.
- Sem número mágico: limite de regra vem de constante com nome.
- Nomes descritivos, sem abreviação, em inglês no código; textos para o usuário em português do Brasil.

Nomes por linguagem
- TypeScript/React: `camelCase` para variáveis, funções e hooks (`useAlgo`); `PascalCase` para componentes, tipos e interfaces; `UPPER_SNAKE_CASE` para constantes de módulo; arquivo de componente em `PascalCase.tsx`, demais em `camelCase.ts`.
- Python: `snake_case` para funções, variáveis e módulos; `PascalCase` para classes; `UPPER_SNAKE_CASE` para constantes.

TypeScript/React
- Componente funcional, um por arquivo, sem `any`; lógica de dados em hook ou service, fora do JSX.
- Coordenadas de região sempre em pixels da imagem; conversão para a tela só na camada de exibição.

Python
- PEP 8 e type hints nas funções públicas.
- Funções puras em `region.py` e `blur.py`; I/O (arquivos temporários, `jpegtran`, HTTP) só nas bordas.

Testes
- Nome no formato cenário e resultado; um comportamento por teste; linha em branco só entre preparação, ação e verificação.
- Imagens de teste são sintéticas, geradas no próprio teste. Nunca commitar fotos reais.

## Verificação antes de commitar
- Backend (em `backend/`): `.venv/Scripts/python -m pytest` com a variável `JPEGTRAN` apontando para o `jpegtran`.
- Frontend (em `frontend/`): `npm run lint`, `npx tsc -b` e `npx vitest run`.
- Não declarar pronto o que não foi verificado. Se algo não foi testado (ex.: comportamento no navegador), dizer.

## Verificação antes de push
Rodar a suíte inteira do backend, `npm run lint`, `npx vitest run` e `npm run build` no frontend. Falhou um, não sobe.

## Git
- Branch única: commits e push direto na `main`. Sem branches de feature, `develop` ou `staging`.
- Nunca force push na `main`.
- Conta do GitHub deste projeto: `GustavoQ-Mateus`. A conta ativa padrão do `gh` na máquina é outra (`Gustavo-QMateus`); usar `GustavoQ-Mateus` só para este repositório e não trocar a conta padrão de forma permanente. Push: `GH_TOKEN=$(gh auth token -u GustavoQ-Mateus) git push`.

## Commits
- Curtos, uma linha, no padrão Conventional Commits: `tipo(escopo): descrição`.
- Tipos: feat, fix, refactor, test, docs, chore, build, ci.
- Escopos: `backend`, `frontend`, `jpeg`, `png`, `webp`, `heic`, `editor`, `api`.
- Descrição no imperativo, minúscula, sem ponto final.
- Exemplos: `feat(jpeg): insere blocos com blur via jpegtran`, `fix(editor): corrige região fora da imagem`, `test(webp): cobre entrada lossy`.
- Um commit por unidade lógica de mudança.
- NUNCA incluir "Co-Authored-By: Claude" nem qualquer referência à Anthropic.

## Segurança e privacidade
- O app roda só em `localhost`; as fotos não saem da máquina. Não adicionar upload para serviços externos, telemetria nem armazenamento das imagens no servidor.
- Nunca commitar segredos, `.env`, credenciais ou fotos pessoais.

## Comunicação
- Responder sempre em português do Brasil.
