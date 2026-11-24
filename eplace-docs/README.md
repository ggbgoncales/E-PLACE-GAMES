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

O site é publicado no GitHub Pages em `https://ggbgoncales.github.io/E-PLACE-GAMES/`, pelo workflow `.github/workflows/docs.yml` (na raiz do repositório): **Actions → Documentação → Run workflow**. Antes, um administrador precisa ativar **Settings → Pages → Source: GitHub Actions**. Se o repositório mudar de dono ou nome, ajuste `url`, `baseUrl`, `organizationName` e `projectName` em `docusaurus.config.js`.
