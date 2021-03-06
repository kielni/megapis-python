const url = new URL(location.href);
const key = url.searchParams.get('u') || 'default';
const items = pegasus(`${config.baseURL}/rss-${key}.json`);

const app = new Vue({ // eslint-disable-line no-unused-vars
  el: '#app',
  data: {
    items: [],
    imageItems: [],
    textItems: [],
    updated: null,
  },

  mounted: function mounted() {
    items.then((data) => {
      const items = data.items.map((item) => {
        let short = item.summary.substr(0, 400);
        const dt = moment(item.date);

        if (item.summary.length > 500) {
          short = short.substr(0, Math.min(short.length, short.lastIndexOf(' '))) + ' ...';
        }
        const obj = Object.assign({
          dateStr: dt.format('MMM DD h:mma'),
          ts: parseInt(dt.format('X')),
          shortSummary: short,
        }, item);
        console.log(obj);
        return obj;
      });
      const grouped = _.groupBy(_.sortBy(items, ['source']), item => item.image ? 'image': 'text');

      this.imageItems = grouped.image;
      this.textItems = grouped.text;
      this.updated = moment(data.updated);
    });
  },

  computed: {
    updatedStr: function updatedStr() {
      return this.updated ? this.updated.format('dddd, MMMM D, h:mm a') : '';
    },
  },

  methods: {
    read: function(ev) {
      // on click href, post url and source to webhook if configured
      if (!config.webhookURL || !config[key].webhook) {
        return;
      }
      const source = $(ev.target).parent().parent().find('.source').text();
      const body = {
        value1: ev.target.href,
        value2: source.replace(/\W+/g, ' '),
        value3: key,
      };

      $.post(config.webhookURL, body);
    },
  },
});
