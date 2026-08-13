document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("diagnostico-form");
  if (!form) return;

  /* Cascada Entidad -> Municipio */
  var entSelect = document.getElementById("ENT");
  var munSelect = document.getElementById("MUN");
  var quiereCorreo = document.getElementById("quiere_correo");
  var emailField = document.getElementById("email-field");
  var emailInput = document.getElementById("email");

  function poblarMunicipios(claveEnt) {
    munSelect.innerHTML = "";
    var lista = (window.MUNICIPIOS && window.MUNICIPIOS[String(claveEnt)]) || [];
    if (!claveEnt || lista.length === 0) {
      var opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Selecciona primero la entidad...";
      munSelect.appendChild(opt);
      munSelect.disabled = true;
      return;
    }
    var placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Selecciona...";
    munSelect.appendChild(placeholder);
    lista.forEach(function (m) {
      var opt = document.createElement("option");
      opt.value = m.clave;
      opt.textContent = m.nombre;
      munSelect.appendChild(opt);
    });
    munSelect.disabled = false;
  }

  if (entSelect && munSelect) {
    entSelect.addEventListener("change", function () {
      poblarMunicipios(entSelect.value);
      clearFieldError(munSelect);
    });
  }

  if (quiereCorreo && emailField && emailInput) {
    quiereCorreo.addEventListener("change", function () {
      emailField.hidden = !quiereCorreo.checked;
      emailInput.required = quiereCorreo.checked;
      if (!quiereCorreo.checked) clearFieldError(emailInput);
    });
  }

  /* ---------------------------- Wizard --------------------------------- */
  var steps = Array.prototype.slice.call(form.querySelectorAll(".wizard-step"));
  if (steps.length === 0) return; // sin JS o markup distinto: no hacemos nada más

  var stepItems = Array.prototype.slice.call(document.querySelectorAll("#stepper .step-item"));
  var stepperNav = document.getElementById("stepper");
  var progressTrack = document.querySelector(".progress-track");
  var progressFill = document.getElementById("progress-fill");
  var stepCount = document.getElementById("step-count");
  var btnPrev = document.getElementById("btn-prev");
  var btnNext = document.getElementById("btn-next");
  var btnSubmit = document.getElementById("btn-submit");
  var btnStart = document.getElementById("btn-start");
  var wizardNav = document.querySelector(".wizard-nav");
  var reviewContent = document.getElementById("review-content");
  var totalSteps = steps.length;
  var current = 0;
  var furthest = 0;

  var STEP_TITLES = [
    "Acceso y privacidad", "Ubicación", "Datos personales",
    "Trayectoria educativa", "Salud, hogar y tecnología"
  ];

  function fieldWrap(el) {
    return el.closest(".field") || el.closest(".checkbox");
  }

  function markInvalid(el) {
    var wrap = fieldWrap(el);
    if (wrap) wrap.classList.add("invalid");
  }

  function clearFieldError(el) {
    var wrap = fieldWrap(el);
    if (wrap) wrap.classList.remove("invalid");
  }

  // Limpia el error en cuanto el usuario corrige el campo
  form.addEventListener("input", function (e) { clearFieldError(e.target); });
  form.addEventListener("change", function (e) { clearFieldError(e.target); });

  function requiredFieldsIn(container) {
    return Array.prototype.slice.call(container.querySelectorAll("[required]"))
      .filter(function (el) { return !el.disabled && el.offsetParent !== null || !el.disabled; });
  }

  function validateStep(index) {
    var step = steps[index];
    var fields = requiredFieldsIn(step);
    var firstInvalid = null;
    fields.forEach(function (el) {
      if (el.disabled) return;
      var valid = el.type === "checkbox" ? el.checked : el.checkValidity();
      if (!valid) {
        markInvalid(el);
        if (!firstInvalid) firstInvalid = el;
      } else {
        clearFieldError(el);
      }
    });
    if (firstInvalid) {
      firstInvalid.focus({ preventScroll: true });
      return false;
    }
    return true;
  }

  function validateWholeForm() {
    var allRequired = Array.prototype.slice.call(form.querySelectorAll("[required]"))
      .filter(function (el) { return !el.disabled; });
    var firstInvalidStep = null;
    allRequired.forEach(function (el) {
      var valid = el.type === "checkbox" ? el.checked : el.checkValidity();
      if (!valid) {
        markInvalid(el);
        if (firstInvalidStep === null) {
          var parentStep = el.closest(".wizard-step");
          if (parentStep) firstInvalidStep = parseInt(parentStep.dataset.step, 10);
        }
      }
    });
    return firstInvalidStep === null ? -1 : firstInvalidStep;
  }

  function labelFor(el) {
    if (el.id) {
      var lbl = form.querySelector('label[for="' + el.id + '"]');
      if (lbl) return lbl.textContent.replace("*", "").trim();
    }
    return el.name;
  }

  function displayValue(el) {
    if (el.tagName === "SELECT") {
      var opt = el.options[el.selectedIndex];
      return opt && opt.value !== "" ? opt.textContent : "—";
    }
    if (el.type === "checkbox") {
      return el.checked ? "Sí" : "No";
    }
    return el.value !== "" ? el.value : "—";
  }

  function buildReview() {
    reviewContent.innerHTML = "";
    steps.forEach(function (step, idx) {
      if (idx === totalSteps - 1) return; // no incluir el propio paso de revisión
      var inputs = Array.prototype.slice.call(
        step.querySelectorAll("input[name], select[name]")
      ).filter(function (el) { return !el.disabled; });
      if (inputs.length === 0) return;

      var group = document.createElement("div");
      group.className = "review-group";

      var heading = document.createElement("h3");
      heading.textContent = STEP_TITLES[idx] || ("Paso " + (idx + 1));
      var editLink = document.createElement("a");
      editLink.href = "#";
      editLink.className = "review-edit";
      editLink.textContent = "Editar";
      editLink.dataset.targetStep = idx;
      heading.appendChild(editLink);
      group.appendChild(heading);

      var table = document.createElement("table");
      table.className = "review-table";
      inputs.forEach(function (el) {
        if (el.type === "checkbox" && el.name === "acepta_privacidad") return; // ya implícito
        var tr = document.createElement("tr");
        var tdLabel = document.createElement("td");
        tdLabel.className = "review-label";
        tdLabel.textContent = labelFor(el);
        var tdValue = document.createElement("td");
        tdValue.textContent = displayValue(el);
        tr.appendChild(tdLabel);
        tr.appendChild(tdValue);
        table.appendChild(tr);
      });
      group.appendChild(table);
      reviewContent.appendChild(group);
    });
  }

  function updateStepper() {
    // En la pantalla de acceso (paso 0) no se muestra el stepper ni la
    // barra de progreso: esa pantalla solo debe mostrar el panel de
    // presentación y la tarjeta de acceso, nada de pasos. Además ocupa
    // toda la pantalla (sin topbar/footer), por eso se marca <body>.
    var enCuestionario = current > 0;
    document.body.classList.toggle("access-mode", !enCuestionario);
    if (stepperNav) stepperNav.hidden = !enCuestionario;
    if (progressTrack) progressTrack.hidden = !enCuestionario;
    if (stepCount) stepCount.hidden = !enCuestionario;
    if (wizardNav) wizardNav.hidden = !enCuestionario;

    stepItems.forEach(function (item) {
      var target = parseInt(item.dataset.stepTarget, 10);
      item.classList.toggle("active", target === current);
      item.classList.toggle("done", target < current);
    });
    var realSteps = totalSteps - 1; // excluye la pantalla de acceso (paso 0)
    var pct = current === 0 ? 0 : ((current - 1) / (realSteps - 1)) * 100;
    if (progressFill) progressFill.style.width = pct + "%";
    if (stepCount && enCuestionario) {
      stepCount.textContent = "Paso " + current + " de " + realSteps;
    }
  }

  function goToStep(index) {
    current = Math.max(0, Math.min(index, totalSteps - 1));
    furthest = Math.max(furthest, current);
    steps.forEach(function (step, idx) {
      step.classList.toggle("active", idx === current);
    });
    updateStepper();
    btnPrev.disabled = current === 0;
    var isLast = current === totalSteps - 1;
    btnNext.hidden = isLast;
    btnSubmit.hidden = !isLast;
    if (isLast) buildReview();
    var card = form.closest(".card") || form;
    card.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  btnNext.addEventListener("click", function () {
    if (!validateStep(current)) return;
    goToStep(current + 1);
  });

  if (btnStart) {
    btnStart.addEventListener("click", function () {
      if (!validateStep(current)) return;
      goToStep(current + 1);
    });
  }

  btnPrev.addEventListener("click", function () {
    goToStep(current - 1);
  });

  stepItems.forEach(function (item) {
    item.addEventListener("click", function () {
      var target = parseInt(item.dataset.stepTarget, 10);
      if (target <= furthest) goToStep(target);
    });
    item.style.cursor = "pointer";
  });

  reviewContent && reviewContent.addEventListener("click", function (e) {
    if (e.target.classList.contains("review-edit")) {
      e.preventDefault();
      goToStep(parseInt(e.target.dataset.targetStep, 10));
    }
  });

  form.addEventListener("submit", function (e) {
    var invalidStep = validateWholeForm();
    if (invalidStep !== -1) {
      e.preventDefault();
      goToStep(invalidStep);
      // Antes esto regresaba al paso con error sin avisar nada, y parecía
      // que el botón "no hacía nada". Ahora se muestra un aviso explícito
      // y se enfoca el primer campo inválido de ese paso.
      window.alert(
        "Falta completar o corregir algún campo en el paso " +
        invalidStep + " (\"" + (STEP_TITLES[invalidStep] || "") + "\"). " +
        "Se resaltó en rojo, revísalo antes de continuar."
      );
      var stepEl = steps[invalidStep];
      var firstInvalidField = stepEl && stepEl.querySelector(".invalid input, .invalid select");
      if (firstInvalidField) firstInvalidField.focus({ preventScroll: true });
    }
  });

  goToStep(0);
});
