# FGSEA gene set enrichment analysis for all phenotypes and with all ATC codes
# Only works if the backend is PostgreSQL because it bypasses the ORM to get
# data directly in R.

library(fgsea)
library(RPostgreSQL)
library(rjson)


db_str <- Sys.getenv("EXPHEWAS_DATABASE_URL")
db_str <- unlist(strsplit(db_str, "//", fixed = T))[2]

pieces <- unlist(strsplit(db_str, ":|@|/"))

username <- pieces[1]
password <- pieces[2]
hostname <- pieces[3]
dbname <- pieces[4]


drv <- dbDriver("PostgreSQL")
con <- dbConnect(drv, dbname = dbname, host = hostname, user = username,
                 password = password)

get_results <- function(outcome_id) {
  # Check if binary or continuous.

  # This is unsafe...
  res <- dbGetQuery(con,
    paste0("select * from outcomes where id='", outcome_id, "'")
  )

  if (length(res) == 0) {
    warning(paste0("Invalid outcome id: ", outcome_id))
    return(NULL)
  }

  if (res[1, "analysis_type"] == "CONTINUOUS_VARIABLE") {
    results_table <- "results_continuous_variables"
  }
  else {
    results_table <- "results_binary_variables"
  }


  res <- dbGetQuery(con, paste0(
    "select gene, p ",
    "from ", results_table, " ",
    "where ",
    " outcome_id='", outcome_id, "' and ",
    " variance_pct=95 ",
    "order by p"
  ))

  res
}


get_all_outcome_ids <- function() {
  dbGetQuery(con,
    paste0("select id from outcomes")
  )$id
}


# Prepare the fgsea data.
atc <- rjson::fromJSON(file = "/Users/legaultmarc/projects/StatGen/exphewas/browser/data/chembl/atc_to_target.json.gz")
atc <- atc$ensembl


for (outcome in get_all_outcome_ids()) {
  # This is a DF with gene, p (already ordered)
  res <- get_results(outcome)

  ranks <- res$p
  names(ranks) <- res$gene

  enrichment <- fgsea(
    pathways = atc,
    stats = ranks,
    minSize = 2,
    maxSize = 500,
    nperm = 10000
  )

  print(enrichment)

}
