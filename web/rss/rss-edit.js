const pageUrl = new URL(location.href);
const key = pageUrl.searchParams.get('u');
const sources = pegasus(`${config.baseURL}/sources-${key}.json`);
const CORS_PROXY = 'https://cors-anywhere.herokuapp.com/';

var vm = new Vue({ // eslint-disable-line no-unused-vars, no-var
  el: '#app',
  data: {
    item: null,
    keyError: !key,
    sources: [],
    addEnabled: false,
    urlError: null,
    sourceUrl: null,
    sourceUrlValidated: false,
    sourceName: null,
    loading: false,
    addMessage: null,
    refreshing: false,
    key,
  },

  mounted: function mounted() {
    // when sources are loaded, create list of url, name sorted by name
    sources.then((data) => {
      this.sources = _.sortBy(Object.keys(data).map(source => ({
        url: source,
        name: data[source].name,
        show: !data[source].hide,
      })), [s => s.name.toLowerCase()]);
    });
  },

  updated: function() {
    $('.uninitialized-toggle').bootstrapToggle();
    $('.uninitialized-toggle').each((idx, toggle) => {
      $(toggle).removeClass('uninitialized-toggle');
    });
  },

  computed: {
    validSource: function() {
      return this.sourceUrlValidated && !this.urlError && this.sourceName && this.sourceName.length;
    },

    feedUrl: function() {
      return `index.html?u=${key}`;
    },
  },

  methods: {
    validateUrl: function() {
      this.urlError = null;
      this.item = null;
      this.sourceUrlValidated = false;
      this.sourceUrl = this.sourceUrl.toLowerCase().trim();

      if (!this.sourceUrl.length) {
        this.urlError = 'Please enter a URL';
        return;
      }
      // check if already in feed
      const dupe = this.sources.find(src => src.url === this.sourceUrl);
      if (dupe) {
        this.urlError = 'URL is already in feed';
        return;
      }

      // parse and set first item (title, shortSummary, sourceLink, source, dateStr) or error
      this.loading = true;
      const parser = new RSSParser();
      parser.parseURL(CORS_PROXY + this.sourceUrl).then((result) => {
        const item = result.items[0];

        this.loading = false;
        this.urlError = null;
        this.sourceUrlValidated = true;
        this.item = {
          title: item.title,
          shortSummary: item.contentSnippet,
          url: item.link,
          source: this.sourceName || '',
          dateStr: moment(item.isoDate).format('MMM DD h:mma'),
        };
      }).catch((error) => {
        this.loading = false;
        this.urlError = `Error parsing URL: ${error.message}`;
        console.error('err', error);
      });
    },

    add: function() {
      const form = document.getElementById('addForm');
      const valid = form.checkValidity() && this.validSource;

      form.classList.add('was-validated');
      if (!valid) {
        return;
      }

      // send url, name, key to lambda
      const body = {
        url: this.sourceUrl,
        name: this.sourceName,
        show: true,
        key,
      };
      console.log('POST ', body);
      // $.post(config.webhookURL, body);
      // add source to sources
      const src = this.sources;

      src.push(body);
      this.sources = _.sortBy(src, [s => s.name.toLowerCase()]);

      document.getElementById('addForm').classList.remove('was-validated');
      this.item = null;
      this.addMessage = `<b>${this.sourceName}</b> added.`;
      setTimeout(() => {
        this.addMessage = null;
      }, 5000);
      this.sourceUrl = '';
      this.sourceName = '';
    },

    _lambda: function(data) {
      return $.post(config.apiURL, data)
        .done((resp) => { console.log('refreshed: ', resp); })
        .fail((resp) => { console.error('error ', resp); });
    },

    toggle: function(checkbox) {
      const url = $(checkbox).attr('data');
      const source = this.sources.find(src => src.url === url);

      source.show = !source.show;
      console.log('toggle ', url, ' show=', source.show);

      this._lambda(JSON.stringify({
        key,
        source: source.url,
        name: source.name,
        hide: source.show ? 'false' : 'true',
        action: 'update',
      }));
    },

    refresh: function() {
      const data = JSON.stringify({
        key,
        action: 'refresh',
      });

      this.refreshing = true;
      this._lambda(data).always(() => { this.refreshing = false; });
    },
  },
});
