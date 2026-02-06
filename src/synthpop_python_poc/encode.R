source("src\\\\synthpop_python_poc\\\\utils-encode_categorical.R")
source("src\\\\synthpop_python_poc\\\\encode_categorical.R")
library(tidyverse)

logger <- function(type, data) {
    #cat(sprintf("\n%s", data))
}
enc <- function(x,y) {
    x[sapply(x, is.character)] <- lapply(x[sapply(x, is.character)], as.factor)
    return(get_encoding(x,y,logger))
}
