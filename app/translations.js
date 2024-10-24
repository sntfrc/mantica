import * as Localization from 'expo-localization';

import { I18n } from "i18n-js";

const i18n = new I18n({
    en: {
        permission: 'Mantica needs to see through your camera',
        grant: 'Make it so'
    },

    it: {
        permission: 'Mantica deve poter vedere la tua fotocamera',
        grant: 'Così sia'
    },
});

i18n.defaultLocale = "en";
i18n.locale = Localization.getLocales()[0].languageCode;
i18n.fallbacks = true;

export default i18n;
