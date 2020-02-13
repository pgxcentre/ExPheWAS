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

  # We convert from p-value to scaled -log10(p).
  res[, 2] <- -log10(res[, 2])

  # If some p-values are numerically 0 we may have infinite values here.
  # We clip them to be a little bit more than the highest finite value.
  max_finite <- max(res[is.finite(res[, 2]), 2])
  res[is.infinite(res[, 2]), 2] <- 1.1 * max_finite

  res[, 2] <- res[, 2] / max(res[, 2])

  # Fix the name to avoid confusion.
  names(res)[2] <- "z"

  res
}


get_all_outcome_ids <- function() {
  dbGetQuery(con,
    paste0("select id from outcomes")
  )$id
}


# Prepare the fgsea data.
atc <- rjson::fromJSON(file = "../data/chembl/atc_to_target.json.gz")
atc <- atc$ensembl

# We limit ourselves to level 4 ATC codes.
atc <- atc[nchar(names(atc)) <= 5]

first = T
for (outcome in get_all_outcome_ids()) {
  res <- get_results(outcome)

  ranks <- res[, 2]  # Weights are equivalent one-sided z-statistics.
  names(ranks) <- res$gene

  enrichment <- fgsea(
    pathways = atc,
    stats = ranks,
    minSize = 2,
    maxSize = 500,
    nperm = 10000
  )

  # Only keep easily serializable columns
  enrichment <- enrichment[, c("pathway", "pval", "padj", "ES", "NES",
                               "nMoreExtreme", "size")]

  # We know that ES should be positive as the highest p-values represent
  # null associations.
  enrichment[enrichment$ES < 0, c("pval", "padj")] <- 1

  enrichment$outcome <- outcome

  if (first) {
    first <- F
    cat("pathway,pval,padj,ES,NES,nMoreExtreme,size,outcome\n",
        file = "atc_fgsea_results.csv")
  }

  write.table(enrichment, file = "atc_fgsea_results.csv", append = T,
              col.names = F, row.names = F, sep = ",")

}
