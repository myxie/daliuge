$( document ).ready(function() {
  // jquery starts here

  //hides the dropdown navbar elements when stopping hovering over the element
  $(".dropdown-menu").mouseleave(function(){
    $(".dropdown-menu").dropdown('hide')
  })

  //deploy physical graph button listener 
  $("#deploy_button").click(function(){
    $("#gen_pg_button").val("Generate &amp; Deploy Physical Graph")
    $("#dlg_mgr_deploy").prop( "checked", true )
    $("#pg_form").submit();
  })

  //erport physical graph button listener
  $("#Pysical_graph").click(function(){
    $("#gen_pg_button").val("Generate Physical Graph")
    $("#dlg_mgr_deploy").prop( "checked", false )
    $("#pg_form").submit();
  })
  
  //get saved settings from local storage or set a default value
  fillOutSettings()

  $('#settingsModal').on('hidden.bs.modal', function () {
    fillOutSettings()
});
});

function saveSettings(){
  var newPort = $("#managerPortInput").val();
  var newHost = $("#managerHostInput").val().replace(/\s+/g, '');
  console.log("Host set to:'"+newHost+"'");
  console.log("Port set to:'"+newPort+"'");

  window.localStorage.setItem("manager_port", newPort);
  window.localStorage.setItem("manager_host", newHost);
  $('#settingsModal').modal('hide')    
}

function fillOutSettings(){
  //get setting values from local storage
  var manager_host = window.localStorage.getItem("manager_host");
  var manager_port = window.localStorage.getItem("manager_port");

  //fill settings with saved or default values
  if (!manager_host){
    $("#managerHostInput").val("localhost");
  }else{
    $("#managerHostInput").val(manager_host);
  };

  if (!manager_port){
    $("#managerPortInput").val("8001");
  }else{
    $("#managerPortInput").val(manager_port);
  };
}

  function makeJSON() {
      console.log("makeJSON()");

      $.ajax({
          url: "/pgt_jsonbody?pgt_name="+pgtName,
          type: 'get',
          error: function(XMLHttpRequest, textStatus, errorThrown) {
            if (404 == XMLHttpRequest.status) {
              console.error('Server cannot locate physical graph file '+pgtName);
            } else {
              console.error('status:' + XMLHttpRequest.status + ', status text: ' + XMLHttpRequest.statusText);
            }
          },
          success: function(data){
            downloadText(pgtName, data);
          }
      });
  }

  function makePNG() {
  
    html2canvas(document.querySelector("#main")).then(canvas => {
      var dataURL = canvas.toDataURL( "image/png" );
      var data = atob( dataURL.substring( "data:image/png;base64,".length ) ),
          asArray = new Uint8Array(data.length);

      for( var i = 0, len = data.length; i < len; ++i ) {
          asArray[i] = data.charCodeAt(i);    
      }

      var blob = new Blob( [ asArray.buffer ], {type: "image/png"} );
      saveAs(blob, pgtName+"_Template.png");
  });
  }

  function createZipFilename(graph_name){
    return graph_name.substr(0, graph_name.lastIndexOf('.graph')) + '.zip';
  }

  function downloadText(filename, text) {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
  }

  // build an object URL from the blob and 'download' it
  function downloadBlob(filename, blob) {
    const url = window.URL.createObjectURL(blob);

    const element = document.createElement('a');
    element.setAttribute('href', url);
    element.setAttribute('download', filename);

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    window.URL.revokeObjectURL(url);
    document.body.removeChild(element);
  }

  function makeCWL() {
    var error = "";

    fetch('/pgt_cwl?pgt_name='+pgtName)
      .then(async resp => {
        // if fetch was not successful, await the error message in the body of the response
        if (resp.status !== 200){
            error = await resp.text();
            return;
        }
        return resp.blob();
      })
      .then(blob => {
        downloadBlob(createZipFilename(pgtName), blob);
      })
      .catch(() => alert(error)); // present error, if it occurred
  }

  function zoomToFit() {
    myDiagram.zoomToFit()
    // console.log(myDiagram.viewportBounds.width.toString());
    // console.log('\n');
    // console.log(myDiagram.viewportBounds.height.toString());
    // console.log('\n -----');
    // console.log(myDiagram.documentBounds.width.toString());
    // console.log('\n');
    // console.log(myDiagram.documentBounds.height.toString());
  }