const path = require('path');

module.exports = {
    entry: ['./src/index.js'],
    output: {
        filename: '[name].js',
        chunkFilename: '[name].js',
        path: path.resolve(__dirname, '../backend/static/build'),
    },
    module: {
        rules: [
        {
            test: /\.css$/i,
            use: ['style-loader', 'css-loader'],
        },
        {
            test: /\.(png|svg|jpg|jpeg|gif)$/i,
            type: 'asset/resource',
        },
        {
            test: /favicon\.ico$/,
            use: ['file-loader']
          },
        ],
    },
};
