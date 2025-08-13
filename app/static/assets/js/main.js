

$(function () {
  "use strict";


  new PerfectScrollbar(".notify-list")

  new PerfectScrollbar(".search-content")


  $(document).ready(function () {
    $("body").addClass("toggled");
  
    $(".btn-toggle").click(function () {
      $("body").toggleClass("toggled");

      if ($("body").hasClass("toggled")) {
        $(".sidebar-wrapper").on("mouseenter", function () {
          $("body").addClass("sidebar-hovered");
        }).on("mouseleave", function () {
          $("body").removeClass("sidebar-hovered");
        });
      } else {
        $(".sidebar-wrapper").off("mouseenter mouseleave");
      }
    });
  
    if ($("body").hasClass("toggled")) {
      $(".sidebar-wrapper").on("mouseenter", function () {
        $("body").addClass("sidebar-hovered");
      }).on("mouseleave", function () {
        $("body").removeClass("sidebar-hovered");
      });
    }
  });
  

  $(function () {
    $('#sidenav').metisMenu();
  });

  $(".sidebar-close").on("click", function () {
    $("body").removeClass("toggled")
  })



  /* dark mode button */

  $(".dark-mode i").click(function () {
    $(this).text(function (i, v) {
      return v === 'dark_mode' ? 'light_mode' : 'dark_mode'
    })
  });


  $(".dark-mode").click(function () {
    $("html").attr("data-bs-theme", function (i, v) {
      return v === 'dark' ? 'light' : 'dark';
    })
  })


  /* sticky header */

  $(document).ready(function () {
    $(window).on("scroll", function () {
      if ($(this).scrollTop() > 60) {
        $('.top-header .navbar').addClass('sticky-header');
      } else {
        $('.top-header .navbar').removeClass('sticky-header');
      }
    });
  });


  /* email */

  $(".email-toggle-btn").on("click", function() {
    $(".email-wrapper").toggleClass("email-toggled")
  }), $(".email-toggle-btn-mobile").on("click", function() {
    $(".email-wrapper").removeClass("email-toggled")
  }), $(".compose-mail-btn").on("click", function() {
    $(".compose-mail-popup").show()
  }), $(".compose-mail-close").on("click", function() {
    $(".compose-mail-popup").hide()
  }), 


  /* chat */

  $(".chat-toggle-btn").on("click", function() {
    $(".chat-wrapper").toggleClass("chat-toggled")
  }), $(".chat-toggle-btn-mobile").on("click", function() {
    $(".chat-wrapper").removeClass("chat-toggled")
  }),



  /* switcher */

  $("#BlueTheme").on("click", function () {
    $("html").attr("data-bs-theme", "blue-theme")
  }),

  $("#LightTheme").on("click", function () {
    $("html").attr("data-bs-theme", "light")
  }),

    $("#DarkTheme").on("click", function () {
      $("html").attr("data-bs-theme", "dark")
    }),

    $("#SemiDarkTheme").on("click", function () {
      $("html").attr("data-bs-theme", "semi-dark")
    }),

    $("#BoderedTheme").on("click", function () {
      $("html").attr("data-bs-theme", "bodered-theme")
    })



  /* search control */

  $(".search-control").click(function () {
    $(".search-popup").addClass("d-block");
    $(".search-close").addClass("d-block");
  });


  $(".search-close").click(function () {
    $(".search-popup").removeClass("d-block");
    $(".search-close").removeClass("d-block");
  });


  $(".mobile-search-btn").click(function () {
    $(".search-popup").addClass("d-block");
  });


  $(".mobile-search-close").click(function () {
    $(".search-popup").removeClass("d-block");
  });




  /* menu active */

  $(function () {
    for (var e = window.location, o = $(".metismenu li a").filter(function () {
      return this.href == e
    }).addClass("").parent().addClass("mm-active"); o.is("li");) o = o.parent("").addClass("mm-show").parent("").addClass("mm-active")
  });



});


/* PROPIOS */

function guardarColeccion() {
  // valores del formulario
  let nombre = document.getElementById("coleccion-nombre").value
  let imagen = document.getElementById("coleccion-imagen").files[0] // Solo el archivo seleccionado
  let categoria = document.getElementById("coleccion-categoria").value

  // Validacion
  if (!nombre || !categoria) {
      mostrarNotificacion("Nombre y categoría son obligatorios", "error")
      return
  }

  // Enviar datos al backend con fetch
  fetch("/guardar_coleccion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
          nombre: nombre,
          imagen: imagen,
          categoria: categoria,
          autor_creacion: "Agustín Riquelme" 
      })
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          // notificacion de exito
          mostrarNotificacion("Colección agregada exitosamente", "success")

          // cerrar el modal
          let modal = bootstrap.Modal.getInstance(document.querySelector("#popup_add_collection"))
          modal.hide()

          // recargar la lista de colecciones sin recargar la página
          setTimeout(() => {
              location.reload() // recarga la página para actualizar la lista
          }, 2000)
      } else {
          mostrarNotificacion(data.message, "error");
      }
  })
  .catch(error => {
      console.error("Error:", error)
      mostrarNotificacion("Ocurrió un error al agregar la colección", "error")
  });
}

// Click en 'Analizar' 

$(function(){
  $('#btn-analizar').click(function(){

    // 1. Validar la selección de una colección
    const coleccionId = $('select[name="coleccion"]').val()

    if (coleccionId === '0') {
      $('#alert-coleccion').show();
      document.getElementById("coleccion").focus()
      return
    }
    $('#alert-coleccion').hide()

     // 2. Validar que haya subidos archivos 
    if (!window.uploadedFiles || window.uploadedFiles.length === 0) {
    $('#alert-sin-audios').show()
      return
    }
    $('#alert-sin-audios').hide()

    // 3. Ocultar el formulario y mostrar progreso
    $('#main-wrapper').addClass('d-none')
    $('#analisis-progress')
      .removeClass('d-none')
      .addClass('d-flex')


  // 4. Lanzar SSE
 let transcriptionStart = null;
let transcriptionTimer = null;

const filesParam = window.uploadedFiles.map(encodeURIComponent).join(',');
const source     = new EventSource(`/analizar_stream/${coleccionId}?files=${filesParam}`);

source.onmessage = e => {
  const data = JSON.parse(e.data);

  if (data.done) {
    // — Detener cronometro al finalizar
    if (transcriptionTimer) {
      clearInterval(transcriptionTimer);
      transcriptionTimer = null;
    }
    $('#status').text('Análisis completado');
    $('#step').text(`Tiempo total: ${data.elapsed}`);
    $('#timer').hide();
    $('#gif_loading').hide();
    $('#ver_resultados').removeClass('d-none').addClass('d-flex');
    source.close();
    return;
  }

  // Status y sub-status principal
  $('#status').text(`Analizando ${data.current}/${data.total}`);
  $('#step').text(`${data.step}...`);

  // Inciar timer al primer 'transcribiendo'
  if (data.step === 'Transcribiendo' && !transcriptionStart) {
    transcriptionStart = Date.now();
    $('#timer').text('00:00').show();

    transcriptionTimer = setInterval(() => {
      const diff = Date.now() - transcriptionStart;
      const secs = Math.floor(diff / 1000);
      const mins = Math.floor(secs / 60);
      const s    = secs % 60;
      const mm   = String(mins).padStart(2, '0');
      const ss   = String(s).padStart(2, '0');
      $('#timer').text(`${mm}:${ss}`);
    }, 1000);
  }
};

source.onerror = () => {
  // Detener en error
  if (transcriptionTimer) {
    clearInterval(transcriptionTimer);
    transcriptionTimer = null;
  }
  $('#status').text('Error durante el análisis.');
  source.close();
};


  });
});










