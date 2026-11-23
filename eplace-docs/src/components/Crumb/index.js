import {useActiveDocContext} from '@docusaurus/plugin-content-docs/client';

const TITULOS = {
  intro: 'Visão geral',
  instalacao: 'Instalação e execução',
  estrutura: 'Estrutura do projeto',
  recordes: 'Recordes',
  'jogos/snake': 'Snake',
  'jogos/pong': 'Pong',
  'jogos/frogger': 'Frogger',
  'jogos/space-invaders': 'Space Invaders',
  'jogos/flappy-bird': 'Flappy Bird',
  'jogos/kombate': 'Kombate',
  sobre: 'Sobre o E-Place',
};

/** Trilha da barra superior: "Documentação / Página atual". */
export default function Crumb() {
  const {activeDoc} = useActiveDocContext(undefined);
  const titulo = (activeDoc && TITULOS[activeDoc.id]) || 'Visão geral';
  return (
    <div className="eplace-crumb">
      Documentação <span style={{color: '#59658f'}}> / </span>
      <b>{titulo}</b>
    </div>
  );
}
