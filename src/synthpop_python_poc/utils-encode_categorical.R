#line 2 is added for testing purposes.
prcomp<-NULL

#' @title Mean Encoding
#' @description Computes a mean encoding for a categorical variable based on the average value of a numerical target.
#' @param x a categorical vector (factor) representing the predictor variable.
#' @param y a numerical vector representing the target variable.
#'
#' @return A dataframe with two columns:
#' \itemize{
#'  \item \code{feature_level}: the level of the categorical variable \code{x}
#'  \item \code{encoding_value}: the mean of \code{y} for each level of \code{x}
#'  }
#' @details This encoding is useful when the target is numeric and you want to preserve
#'  target-related structure in the categorical predictor.
#'
#'  Called by \code{\link{get_encoding}}.
#'
#'
mean_encode <- function(x,y){

  df <- data.frame(x = x, y=y)
  encoding_map <- aggregate(df['y'], by = df['x'], FUN = mean, na.rm = TRUE)
  colnames(encoding_map) <- c('feature_level', '1')
  return(encoding_map)
}

#' @title PCA Encoding
#' @description Transforms a categorical variable into one or more numeric features using Principal Component Analysis (PCA),
#' based on how the levels of the categorical predictor co-occur with levels of the categorical target.
#'
#' First, a count matrix is created showing how often each level of \code{x} (predictor/feature) co-occurs with each level
#' of \code{y} (target). PCA is then applied to this matrix, and the result is used as a numerical encoding.
#'
#' @param x a categorical vector (factor) of the predictor to be encoded.
#' @param y the categorical target variable.
#'
#' @return A named list with:
#' \itemize{
#'  \item \code{encoding}: A tibble with one row per level of \code{x}, and one column per principal component. The first column is the \code{feature_level}.
#'  \item \code{sdev}: The standard deviations of the principal components (from \code{prcomp}).
#'  }
#' @details
#' Levels of \code{x} that appear with similar distributions across \code{y} levels will have similar encodings.
#' The variance of the co-occurence matrix is used to decide whether scaling is applied.
#'
#' Called by \code{\link{get_encoding}}.
#'
#' @import tidyr
#' @importFrom tidyr pivot_wider
pca_encode <- function(x,y){

  df <- data.frame(x = x, target=y)
  feature_target_counts <- df %>%
    drop_na(x) %>%
    group_by(x,target) %>%
    summarise(target_count = n(), .groups = "drop") %>%
    select(x,target, target_count) %>%
    ungroup() %>%
    pivot_wider(names_from=target,
                names_prefix = "pca_encoding_",
                values_from=target_count,
                values_fill = 0)

  variances <- as.factor(apply(feature_target_counts %>% select(-x), 1, var) != 0)
  pc <- prcomp(t(feature_target_counts %>% select(-x)),center= TRUE,scale=variances)

  encoding <- tibble(feature_level = feature_target_counts$x,as_tibble((pc$rotation),.name_repair = "unique"))

  result = list(encoding = encoding, sdev = pc$sdev)
  return(result)

}

#' @title Select Number of Principal Components
#' @description
#' Determines the number of principal components needed to retain at least 95% of the total variance
#' in a PCA result. This is used to reduce dimensionality while preserving most of the information.
#' @param sdev a numeric vector of standard deviations of the principal components.
#' @return An integer: the number of principal components required to explain at least 95% of the variance.
#' @details This funcion accumulates the explained variance and selects the minimum number of components
#' whose cumulative variance exceeds or equals 95% of the total.
#'
#' Called by \code{\link{get_encoding}} to decide how many components to retain from \code{\link{pca_encode}}.
#'
number_of_principal_components<- function(sdev){
  accumulated <- sdev %>% accumulate(`+`)
  threshold <- accumulated %>% tail(n=1)*0.95

  result <- accumulated %>% keep(\(x) x <= threshold) %>%length()

  if (result == 0){
    return(1)
  }

  if(accumulated[result] < threshold ){

    return(result+1)
  }

  return(result)
}

#' @title Compute Encoding for Categorical Predictors
#' @description
#' Automatically selects and computes an appropriate encoding method for a categorical variable \code{x},
#' given a target variable \code{y}. This function chooses between:
#' \itemize{
#'  \item Mean encoding (if \code{y} is numeric)
#'  \item PCA encoding with all components
#'  \item PCA encoding with a reduced number of components
#' }
#' @param x a categorical vector (factor or character) of the predictors to be encoded.
#' @param y the target variable.
#' @param logger A function to handle log messages. This function should take 2 arguments. See \link[syn.EncodedCart]{syn.EncodedCart}
#' @return A dataframe with the encoded version of \code{x}. It has one or more numeric columns depending on the strategy used.
#' @details
#' Strategy selection:
#' \itemize{
#'  \item If both \code{x} and \code{y} have more than 30 levels → PCA encoding with reduced components (via \code{\link{number_of_principal_components}})
#'  \item If \code{y} is categorical and has <= 30 levels → PCA encoding with all components
#'  \item Else (e.g., if \code{y} is numeric) → Mean encoding
#' }
#'
#' Internally calls: \code{\link{pca_encode}}, \code{\link{number_of_principal_components}}, and \code{\link{mean_encode}}.
#'
#' Called by: \code{\link{encode_categorical}}.
#'
get_encoding <- function(x,y,logger){

    logger("performance",sprintf('"encoding-workload":{
                                      "levels-feature":%i,
                                      "levels-target":%i,
                                      "n_rows":%i
                                 }',nlevels(x),nlevels(y),length(x)))
    if(nlevels(x) >30 & nlevels(y) > 30){
      logger("info","'encoding-type':'PCA-reduced'")
      pca_result <-pca_encode(x,y)
      number_of_pcs <-number_of_principal_components(pca_result$sdev)
      logger("performance",sprintf('
                                   pca-result:{
                                        "total-component-count":%i,
                                        "used-component-count":%i,
                                        "mean-sdev":%f,
                                        "sdev-sdev":%f
                                   }',length(pca_result$sdev)
                                   ,number_of_pcs
                                   ,mean(pca_result$sdev)
                                   ,sd(pca_result$sdev)))
      return(pca_result$encoding[,0:number_of_pcs+1])
    }
    if(class(y)=="factor" & nlevels(y) <= 30){
      logger("info","'encoding-type':'PCA-full'")
      pca_result <- pca_encode(x,y)
      logger("performance",sprintf('
                                   pca-result:{
                                        "total-component-count":%i,
                                        "used-component-count":%i,
                                        "mean-sdev":%f,
                                        "sdev-sdev":%f
                                   }',length(pca_result$sdev)
                                   ,length(pca_result$sdev)
                                   ,mean(pca_result$sdev)
                                   ,sd(pca_result$sdev)))
      return(pca_result$encoding)
    }
    logger("info","'encoding-type':'mean encode'")
    return(mean_encode(x,y))
}

#' @title Apply Encoding to Categorical Column
#' @description
#' Applies a precomputed encoding to a categorical variable. This merges the original values
#' with their corresponding encoded numerical representations, based on a lookup table.
#' @param column A categorical vector (factor or character) that needs to be encoded.
#' @param encoding A dataframe or tibble containing the encoding map. The first column should be
#' \code{feature_level}, and the remaining columns are numeric encodings (e.g., from PCA or mean encoding).
#' @return A tibble with one or more numeric columns representing the encoded values of \code{column}.
#' The order of the rows is preserved.
#'
#' @details
#' The function merges the original values of \code{column} with the corresponding encodings
#' from the table \code{encoding}, through a \code{left_join}. Then it removes the categorical value.
#'
#' Called by: \code{\link{encode_categorical}}.
#'
apply_encoding_column<- function(column,encoding){
  return(tibble(feature_level=column) %>% left_join(encoding,by='feature_level') %>% select(-feature_level))
}

#' @title resample
#' @description
#' This function is copied from synthpop to make the EncodedCart function work.
resample <- function(x, ...) x[sample.int(length(x), ...)]
