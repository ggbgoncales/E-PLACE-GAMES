// @ts-check
import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'E-Place | Documentação Arcade',
  tagline: 'Python Offline Arcade — clássicos, desafios e diversão.',
  favicon: 'img/favicon.png',

  future: {
    v4: true,
  },

  // Publicação no GitHub Pages: https://ggbgoncales.github.io/E-PLACE-GAMES/
  url: 'https://ggbgoncales.github.io',
  baseUrl: '/E-PLACE-GAMES/',
  organizationName: 'ggbgoncales',
  projectName: 'E-PLACE-GAMES',
  trailingSlash: false,

  onBrokenLinks: 'throw',

  stylesheets: [
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap',
  ],

  i18n: {
    defaultLocale: 'pt-BR',
    locales: ['pt-BR'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          // A documentação ocupa o site inteiro, como na versão original.
          routeBasePath: '/',
        },
        blog: false,
        pages: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/logo.png',
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: true,
        respectPrefersColorScheme: false,
      },
      docs: {
        sidebar: {
          hideable: false,
          autoCollapseCategories: false,
        },
      },
      navbar: {
        hideOnScroll: false,
        items: [
          {type: 'custom-crumb', position: 'left'},
          {
            type: 'html',
            position: 'right',
            value: '<span class="eplace-pill">✦ ARCADE EDITION</span>',
          },
        ],
      },
      footer: {
        style: 'dark',
        copyright:
          '<span>© E-Place · Projeto acadêmico de mini-games arcade 2D</span><span>Feito com 💜, Python e espírito retrô.</span>',
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'python', 'json'],
      },
    }),
};

export default config;
