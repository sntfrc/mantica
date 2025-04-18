import * as Localization from 'expo-localization';

import { I18n } from "i18n-js";

const i18n = new I18n({
    en: {
    },

    it: {
    },
});

i18n.defaultLocale = "en";

const loc = Localization.getLocales();
if (loc == null || loc.length == 0) {
    i18n.locale = "en";
} else {
    i18n.locale = Localization.getLocales()[0].languageCode;
}

i18n.fallbacks = true;

export default i18n;
