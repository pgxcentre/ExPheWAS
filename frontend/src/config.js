
export const URL_PREFIX = process.env.ASSET_PATH.replace(/\/$/, "");
export const API_URL = URL_PREFIX + "/api";
export const DT_API_URL = URL_PREFIX + "/dt";
export const ICD10_URL = "https://icd.who.int/browse10/2016/en#";
export const UNIPROT_URL = "https://www.uniprot.org/uniprot";
export const ATC_API_URLS = {
  fgsea: '/enrichment/atc/fgsea',
  fisher: '/enrichment/atc/contingency'
};
