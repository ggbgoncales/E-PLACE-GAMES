# Documentação do E-Place

Site de documentação feito com [Docusaurus](https://docusaurus.io/) (precisa de Node.js 20 ou superior).

## Rodar localmente

```bash
npm install
npm start
```

O site abre em `http://localhost:3000/E-PLACE-GAMES/`.

## Gerar a versão final

```bash
npm run build
npm run serve
```

## Onde editar

| O quê | Onde |
|---|---|
| Páginas | `docs/` (Markdown) |
| Menu lateral | `sidebars.js` |
| Endereço e configurações do site | `docusaurus.config.js` |
| Visual (cores, layout) | `src/css/custom.css` |
| Página "Visão geral" | `src/components/Overview/` |
| Capas e capturas de tela | `static/img/` |

## Publicação

O site é estático: `npm run build` gera a pasta `build/`, que pode ser publicada em qualquer hospedagem (por exemplo, o GitHub Pages). A configuração atual aponta para `https://ggbgoncales.github.io/E-PLACE-GAMES/`. Se o repositório mudar de dono ou nome, ajuste `url`, `baseUrl`, `organizationName` e `projectName` em `docusaurus.config.js`.
