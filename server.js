// > node server.js 8888
var port = 2222;
if (process.argv.length > 2) port = parseInt(process.argv[2]);

const bodyParser = require('body-parser');
const express = require('express');
const fs = require('fs');
const app = express();

app.use(express.urlencoded({ extended: true }));
app.use(express.static('./')); //Tells the app to serve static files from ./
app.use(bodyParser.json());

// // Listen for data
// app.post('/save', function (req, res) {
//   var filename = "."+req.body.filename;
//   var data = req.body.data;
//   // write to file
//   fs.writeFile(filename, JSON.stringify(data), 'utf8', function(err, d){
//     console.log('Wrote data to file');
//   });
//
//   // return response
//   res.send({
//     status: 1,
//     message: "Success"
//   });
// });

app.listen(port, () => console.log('Listening on port '+port));
