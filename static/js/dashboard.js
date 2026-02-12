/* ============================
      Modais
============================ */

function abrirAddEntrada() {
    document.getElementById("modalAddEntrada").style.display = "flex";
}

function abrirAddDespesa() {
    document.getElementById("modalAddDespesa").style.display = "flex";
}

function abrirEditar(id, tipo, valor, descricao, data_raw) {
    document.getElementById("modalEdit").style.display = "flex";

    document.getElementById("edit-id").value = id;
    document.getElementById("edit-tipo").value = tipo;
    document.getElementById("edit-valor").value = valor;
    document.getElementById("edit-descricao").value = descricao;

    if (data_raw) {
        try {
            let d = data_raw.replace(" ", "T");
            document.getElementById("edit-data").value = d;
        } catch {
            document.getElementById("edit-data").value = "";
        }
    }
}

function abrirDelete(id, tipo) {
    document.getElementById("modalDelete").style.display = "flex";
    document.getElementById("delete-id").value = id;
    document.getElementById("delete-tipo").value = tipo;
}

function fecharModais() {
    document.querySelectorAll(".modal-bg").forEach(m => {
        m.style.display = "none";
    });
}


/* ============================
      Gráfico Linha
============================ */

if (document.getElementById("graficoLinha")) {
    new Chart(document.getElementById("graficoLinha"), {
        type: "line",
        data: {
            labels: window.labels_linha,
            datasets: [
                {
                    label: "Entradas",
                    borderColor: "#26d13a",
                    borderWidth: 2,
                    tension: 0.3,
                    data: window.entradas_linha
                },
                {
                    label: "Despesas",
                    borderColor: "#ff3e3e",
                    borderWidth: 2,
                    tension: 0.3,
                    data: window.despesas_linha
                }
            ]
        },
        options: {
            plugins: { legend: { labels: { color: "#fff" } } },
            scales: {
                x: { ticks: { color: "#ddd" } },
                y: { ticks: { color: "#ddd" } }
            }
        }
    });
}


/* ============================
      Tema
============================ */

function toggleTheme() {
    document.body.classList.toggle("dark");
}
