# rdfa-annotation-client
Javascript annotation client for RDFa enriched web resources

## How to install

Clone the repository:
```
git clone https://github.com/marijnkoolen/rdfa-annotation-client.git
```

Install the required npm packages:
```
npm install
```

Install the required python packages:
```
pip install
```

## How to test

Start the server:
```
python test-server.py
```

and point your browser to `localhost:3000`

## How to modify

Run the webpack watcher:
```
npm run dev
```

Whenever you modify source files in `src/`, the watcher will rebuild the Javascript bundle `public/js/rdfa-annotation-client.js` that’s used in the test letter `public/testletter.html`.

