(function () {
    const root = document.querySelector("[data-catalogo-url]");
    if (!root) return;

    const url = root.getAttribute("data-catalogo-url");
    const busca = document.getElementById("catalogo-busca");
    const lista = document.getElementById("catalogo-resultados");
    const aviso = root.querySelector("[data-catalogo-escolhido]");
    const filtroClube = document.getElementById("catalogo-clube");
    const filtroPosicao = document.getElementById("catalogo-posicao");
    const filtroFuncao = document.getElementById("catalogo-funcao");
    const form = root.closest("form");
    const posicaoInicial = root.getAttribute("data-posicao") || "";
    let timer = null;
    let atletas = [];

    if (!busca || !lista || !form) return;

    function campo(name) {
        return form.querySelector('[name="' + name + '"]');
    }

    function preencher(atleta) {
        const set = function (name, value) {
            const el = campo(name);
            if (el && value !== null && value !== undefined && value !== "") {
                el.value = value;
            }
        };
        set("catalog_id", atleta.id);
        set("nome", atleta.nome);
        set("clube", atleta.clube_id);
        set("posicao", atleta.posicao);
        set("funcao", atleta.funcao || atleta.posicao);
        if (atleta.numero) set("numero", atleta.numero);
        set("gols", atleta.gols);
        lista.hidden = true;
        lista.innerHTML = "";
        busca.value = atleta.nome;
        if (aviso) {
            aviso.textContent = atleta.nome + " · " + atleta.clube_nome + " · " + (atleta.funcao_label || atleta.posicao_label);
        }
    }

    const ORDEM_SETOR = ["GOL", "ZAG", "LAT", "MEI", "ATA"];

    function render(items) {
        atletas = items;
        if (!items.length) {
            lista.hidden = false;
            lista.innerHTML = '<p class="campo-form__ajuda">Nenhum atleta encontrado neste filtro.</p>';
            return;
        }
        const grupos = {};
        items.forEach(function (a) {
            const chave = a.posicao || "MEI";
            (grupos[chave] = grupos[chave] || []).push(a);
        });
        let html = "";
        ORDEM_SETOR.forEach(function (sigla) {
            const bloco = grupos[sigla];
            if (!bloco) return;
            const rotulo = bloco[0].posicao_label || sigla;
            html += '<p class="catalogo-grupo">' + rotulo + " · " + bloco.length + "</p>";
            html += bloco.map(function (a) {
                const funcao = a.funcao_label || a.posicao_label || a.posicao;
                return (
                    '<button type="button" class="catalogo-item" data-id="' + a.id + '">' +
                    '<span class="catalogo-item__nome">' + a.nome + "</span>" +
                    '<span class="catalogo-item__meta">' + a.clube + " · " + funcao + " · " + a.gols + " gols</span>" +
                    "</button>"
                );
            }).join("");
        });
        lista.hidden = false;
        lista.innerHTML = html;
        lista.querySelectorAll(".catalogo-item").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const atleta = atletas.find(function (x) { return String(x.id) === btn.getAttribute("data-id"); });
                if (atleta) preencher(atleta);
            });
        });
    }

    function sincronizarFuncoes() {
        if (!filtroFuncao || !filtroPosicao) return;
        const mapa = {
            GOL: [["GOL", "Goleiro"]],
            ZAG: [["ZAG", "Zagueiro"]],
            LAT: [["LD", "Lateral direito"], ["LE", "Lateral esquerdo"], ["LAT", "Lateral"]],
            MEI: [["VOL", "Volante"], ["MC", "Meia central"], ["MAT", "Meia-atacante"], ["MD", "Meia direita"], ["ME", "Meia esquerda"], ["MEI", "Meia"]],
            ATA: [["PD", "Ponta direita"], ["PE", "Ponta esquerda"], ["SA", "Segundo atacante"], ["CA", "Centroavante"], ["ATA", "Atacante"]],
        };
        const setor = filtroPosicao.value;
        const atual = filtroFuncao.value;
        const opcoes = setor ? (mapa[setor] || []) : Object.keys(mapa).reduce(function (acc, k) {
            return acc.concat(mapa[k]);
        }, []);
        filtroFuncao.innerHTML = '<option value="">Todas</option>';
        opcoes.forEach(function (par) {
            const opt = document.createElement("option");
            opt.value = par[0];
            opt.textContent = par[1];
            if (par[0] === atual) opt.selected = true;
            filtroFuncao.appendChild(opt);
        });
    }

    function consultar() {
        const params = new URLSearchParams();
        const q = busca.value.trim();
        if (q) params.set("q", q);
        const clube = filtroClube && filtroClube.value;
        if (clube) params.set("clube", clube);
        const posicao = (filtroPosicao && filtroPosicao.value) || posicaoInicial;
        if (posicao) params.set("posicao", posicao);
        const funcao = filtroFuncao && filtroFuncao.value;
        if (funcao) params.set("funcao", funcao);
        lista.hidden = false;
        lista.innerHTML = '<p class="campo-form__ajuda">Buscando…</p>';
        fetch(url + "?" + params.toString(), { headers: { Accept: "application/json" } })
            .then(function (resposta) {
                if (!resposta.ok) throw new Error("falha");
                return resposta.json();
            })
            .then(function (data) { render(data.atletas || []); })
            .catch(function () {
                lista.hidden = false;
                lista.innerHTML = '<p class="campo-form__erro">Não foi possível carregar o catálogo agora.</p>';
            });
    }

    busca.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(consultar, 180);
    });
    busca.addEventListener("focus", consultar);
    [filtroClube, filtroFuncao].forEach(function (el) {
        if (el) el.addEventListener("change", consultar);
    });
    if (filtroPosicao) {
        filtroPosicao.addEventListener("change", function () {
            if (filtroFuncao) filtroFuncao.value = "";
            sincronizarFuncoes();
            consultar();
        });
        sincronizarFuncoes();
    }
})();
