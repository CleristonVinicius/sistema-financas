/* ============================
      Modais
============================ */

// Fechar modal ao clicar no fundo
document.querySelectorAll(".modal-bg").forEach(modal => {
    modal.addEventListener("click", e => {
        if (e.target === modal) modal.style.display = "none";
    });
});

// Abrir modais
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
        let valor_formatado = data_raw.replace(" ", "T").slice(0, 16);
        document.getElementById("edit-data").value = valor_formatado;
    }
}

function abrirDelete(id, tipo) {
    const modal = document.getElementById("modalDelete");
    modal.style.display = "flex";

    document.getElementById("delete-id").value = id;
    document.getElementById("delete-tipo").value = tipo;
}

// Fechar modais
function fecharModais() {
    document.querySelectorAll(".modal-bg").forEach(m => {
        m.style.display = "none";
    });
}

// Confirmações
function confirmarAddEntrada() {
    document.getElementById("formAddEntrada").submit();
}

function confirmarAddDespesa() {
    document.getElementById("formAddDespesa").submit();
}

function confirmarEditar() {
    document.getElementById("formEdit").submit();
}

function confirmarDelete() {
    document.getElementById("formDelete").submit();
}
