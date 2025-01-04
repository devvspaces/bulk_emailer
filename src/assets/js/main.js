const fileInput = document.getElementById("csv");

const previewCSVData = async (dataurl) => {
  const d = await d3.csv(dataurl);
  console.log({
    d,
  });
  console.log(d.columns);

  const email_key = document.getElementById("email_key");
  // delete previous options
  email_key.options.length = 0;

  d.columns.map((col) => {
    email_key.options[email_key.options.length] = new Option(col, col);
  });

  $(function () {
    $("#slider-range").slider({
      range: true,
      min: 0,
      max: d.length,
      values: [0, d.length],
      slide: function (event, ui) {
        $("#start").val(ui.values[0]);
        $("#stop").val(ui.values[1]);
      },
    });
    $("#start").val($("#slider-range").slider("values", 0));
    $("#stop").val($("#slider-range").slider("values", 1));
  });
};

const readFile = (e) => {
  const file = fileInput.files[0];
  if (!file) {
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    const dataUrl = reader.result;
    previewCSVData(dataUrl);
  };
  reader.readAsDataURL(file);
};

if (fileInput) {
  fileInput.onchange = readFile;
}
