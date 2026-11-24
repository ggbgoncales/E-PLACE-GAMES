// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    {
      type: 'category',
      label: 'COMECE AQUI',
      collapsible: false,
      collapsed: false,
      items: [
        {type: 'doc', id: 'intro', label: '⌂  Visão geral'},
        {type: 'doc', id: 'instalacao', label: '⚙  Instalação e execução'},
        {type: 'doc', id: 'estrutura', label: '▤  Estrutura do projeto'},
        {type: 'doc', id: 'recordes', label: '🏆  Recordes'},
      ],
    },
    {
      type: 'category',
      label: 'MINI-GAMES',
      collapsible: false,
      collapsed: false,
      items: [
        {type: 'doc', id: 'jogos/snake', label: '🐍  Snake'},
        {type: 'doc', id: 'jogos/pong', label: '🏓  Pong'},
        {type: 'doc', id: 'jogos/frogger', label: '🐸  Frogger'},
        {type: 'doc', id: 'jogos/space-invaders', label: '👾  Space Invaders'},
        {type: 'doc', id: 'jogos/flappy-bird', label: '🐤  Flappy Bird'},
        {type: 'doc', id: 'jogos/kombate', label: '🥊  Kombate'},
      ],
    },
    {
      type: 'category',
      label: 'PROJETO',
      collapsible: false,
      collapsed: false,
      items: [{type: 'doc', id: 'sobre', label: '✦  Sobre o E-Place'}],
    },
  ],
};

export default sidebars;
