const webpack = require('webpack');
const path = require('path');

const ASSET_PATH = process.env.EXPHEWAS_URL_ROOT || "/";
const OUTPUT_PATH = process.env.WEBPACK_OUTPUT_PATH || "dist";

module.exports = {
  module: {
    rules: [
      { test: /\.js$/, exclude: /node_modules/, loader: "babel-loader" },
      { test: /\.css$/, use: ["style-loader", "css-loader"] },
      {
        test: /\.scss$/,
        use: [
          {
            loader: 'style-loader', // inject CSS to page
          },
          {
            loader: 'css-loader', // translates CSS into CommonJS modules
          },
          {
            loader: 'postcss-loader', // Run post css actions
            options: {
              plugins: function () { // post css plugins, can be exported to postcss.config.js
                return [
                  require('precss'),
                  require('autoprefixer')
                ];
              }
            }
          },
          {
            loader: 'sass-loader' // compiles Sass to CSS
          }
        ]
      },
      { test: /.png$/, loader: 'file-loader', options: { publicPath: ASSET_PATH.replace(/\/$/, '') + "/dist" } }
    ]
  },
  externals: {
    jquery: 'jQuery'
  },
  plugins: [
    new webpack.DefinePlugin({'process.env.ASSET_PATH': JSON.stringify(ASSET_PATH)}),
  ],
  resolve: {
    mainFields: ['modules', 'main', 'browser']
  },
  output: {
    path: path.resolve(__dirname, OUTPUT_PATH)
  },
  node: {
    fs: 'empty',
    net: 'empty'
  }
}
