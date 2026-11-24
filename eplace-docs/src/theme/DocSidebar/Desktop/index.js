import Desktop from '@theme-original/DocSidebar/Desktop';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';

function filtrar(valor) {
  const q = valor.toLowerCase().trim();
  document.querySelectorAll('.theme-doc-sidebar-menu .theme-doc-sidebar-item-link').forEach((item) => {
    item.style.display = !q || item.innerText.toLowerCase().includes(q) ? '' : 'none';
  });
}

/** Barra lateral como a da documentação original: logo, busca, grupos e rodapé. */
export default function DesktopWrapper(props) {
  const logo = useBaseUrl('/img/logo.png');
  return (
    <div className="eplace-side">
      <Link className="eplace-brand" to="/" aria-label="E-Place — página inicial">
        <img src={logo} alt="Logo E-Place — Python Offline Arcade" />
      </Link>
      <input
        className="eplace-search"
        placeholder="⌕  Buscar na documentação..."
        aria-label="Buscar na documentação"
        onChange={(e) => filtrar(e.target.value)}
      />
      <Desktop {...props} />
      <div className="eplace-sidefoot">
        DOCUMENTAÇÃO DO PROJETO
        <br />
        <span style={{color: 'var(--cyan)'}}>●</span> Versão acadêmica · Python + Pygame
      </div>
    </div>
  );
}
