import Link from '@docusaurus/Link';

import styles from './styles.module.css';

const JOGOS = [
  {id: '01', icone: '🐍', nome: 'Snake', to: '/jogos/snake', texto: 'Coma as frutas, faça combos e evite colidir com as paredes ou com o próprio corpo.'},
  {id: '02', icone: '🏓', nome: 'Pong', to: '/jogos/pong', texto: 'Controle sua raquete e vença a disputa de reflexos contra a CPU ou um amigo. Vence quem chegar a 7.'},
  {id: '03', icone: '🐸', nome: 'Frogger', to: '/jogos/frogger', texto: 'Ajude o sapo a atravessar rios perigosos em fases infinitas, pulando em troncos e tartarugas.'},
  {id: '04', icone: '👾', nome: 'Space Invaders', to: '/jogos/space-invaders', texto: 'Pilote a nave, destrua inimigos e asteroides e sobreviva a ondas cada vez mais intensas.'},
  {id: '05', icone: '🐤', nome: 'Flappy Bird', to: '/jogos/flappy-bird', texto: 'Controle o voo do passarinho, passe pelos canos, junte moedas e personalize-o na loja.'},
  {id: '06', icone: '🥊', nome: 'Kombate', to: '/jogos/kombate', texto: 'Luta 1 contra 1 com seis lutadores, quatro arenas e combos. Enfrente a CPU ou um amigo.'},
];

/** Página "Visão geral": mesma estrutura da documentação original. */
export default function Overview() {
  return (
    <div>
      <div className={styles.hero}>
        <div className={styles.eyebrow}>▰ DOCUMENTAÇÃO OFICIAL DO PROJETO</div>
        <h1 className={styles.title}>
          O seu próximo
          <br />
          <span className={styles.gradient}>recorde começa aqui.</span>
        </h1>
        <p className={styles.lead}>
          Bem-vindo ao E-Place: uma coletânea de mini-games arcade 2D que reúne a nostalgia dos
          clássicos em um só lugar. Explore os jogos, conheça o projeto e prepare-se para superar
          seus próprios limites.
        </p>
        <div className={styles.buttons}>
          <Link className={styles.btn} to="/instalacao">▶ Começar agora</Link>
          <Link className={`${styles.btn} ${styles.secondary}`} to="/sobre">Conheça o projeto ↗</Link>
        </div>
      </div>

      <div className={styles.sectionHead}>
        <div>
          <h2>Selecione seu desafio</h2>
          <p>Clássicos retrô. Novos recordes. Diversão sem pausa.</p>
        </div>
        <span className={styles.tag}>6 MINI-GAMES</span>
      </div>

      <div className={styles.grid}>
        {JOGOS.map((j) => (
          <article key={j.id} className={styles.card}>
            <div className={styles.cardTop}>
              <div className={styles.icon}>{j.icone}</div>
              <span className={styles.num}>GAME_{j.id}</span>
            </div>
            <h3>{j.nome}</h3>
            <p>{j.texto}</p>
            <Link className={styles.textLink} to={j.to}>Explorar documentação →</Link>
          </article>
        ))}
      </div>

      <div className={styles.sectionHead}>
        <div>
          <h2>Sobre esta documentação</h2>
          <p>O essencial para conhecer, executar e entender o E-Place.</p>
        </div>
      </div>
      <div className={styles.features}>
        <div className={styles.feature}>⚙️<b>Instalação</b><span>Prepare o Python, instale dependências e execute o projeto.</span></div>
        <div className={styles.feature}>🧩<b>Arquitetura</b><span>Entenda como o launcher encontra e executa os mini-games.</span></div>
        <div className={styles.feature}>🏆<b>Experiência arcade</b><span>Uma coleção de desafios com recordes e identidade visual retrô.</span></div>
      </div>
    </div>
  );
}
