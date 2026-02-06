#'@title Encode Categorical Variable
#'@description This function is called by \code{\link{syn.EncodedCart}} to prepare categorical predictors before synthesis.
#'It applies an encoding algorithm to a categorical variable in both the observed (`x`)
#'and already synthesized (`xp`) data. Depending on the characteristics of the variable
#'and the target, this function automatically chooses between:
#'- No encoding (if the number of levels is small)
#'- Mean encoding
#'- PCA with all components
#'- PCA with a reduced number of components
#'@param x the observed (original) data column for the variable to encode (features).
#'@param xp the corresponding column in the already synthesized data.
#'@param target the target variable to be synthesized; used for deriving encodings.
#'@param feature_name the name (string) of the variable being encoded; used to  name resulting encoded columns to avoid collisions.
#'@param logger A function to handle log messages. This function should take 2 arguments. See \link[syn.EncodedCart]{syn.EncodedCart}
#'@details If the number of levels in `x` is 15 or fewer, no encoding is applied. Otherwise, encoding is chosen based on the type and number of levels in 'target'. Column names of the encoded variables are prefixed with `feature_name` to prevent naming collisions.
#'This function is intended to be defined before the synthesis, as it is called during.
#'
#'Internally calls: \code{\link{get_encoding}}, \code{\link{apply_encoding_column}}.
#'
#'Called by: \code{\link{syn.EncodedCart}} to prepare categorical predictors before synthesis.
#'@return A named list with two data frames:
#'\item{`x`}{Encoded version of the observed data.}
#'\item{`xp`}{Encoded version of the synthesized data.}
#'@seealso \code{\link{syn.EncodedCart}}
encode_categorical <- function(x,xp,target,feature_name,logger){

  #todo: make sure that characters are factors

    if(nlevels(x)>0){
      encoding <- get_encoding(x,target,logger)

      x_enc<-apply_encoding_column(x,encoding)
      xp_enc <- apply_encoding_column(xp,encoding)

      colnames(x_enc) <- paste(feature_name,colnames(x_enc),sep="_")
      colnames(xp_enc) <- paste(feature_name,colnames(xp_enc),sep="_")
      return(list(
        x = x_enc,
        xp = xp_enc))
    }
  else{
    logger("info","'encoding-type42':'none'")

    x_enc <-data.frame(x=x)
    xp_enc <- data.frame(xp=xp)

    colnames(x_enc) <- feature_name
    colnames(xp_enc) <- feature_name

    return(list(
      x = x_enc,
      xp = xp_enc))
  }

}



#' @title Encoded CART Synthesis Method
#' @description Applies CART synthesis after encoding categorical predictors using PCA or mean encoding.
#'This function wraps \code{\link[synthpop]{syn.cart}} and includes preprocessing for categorical variables
#'with many levels.
#'
#'This function can be used a synthesis method in the \code{\link[synthpop]{syn.cart()}} framework by specifying \code{method = "EncodedCart"}.
#'
#'All parameters that are relevant to the synthpop implementation of CART should be prefixed with "cart.".
#'
#' @param y an original data vector of length {`n`} representing the target.
#' @param x a matrix ({`n`} x {`p`}) of original features used for fitting. \code{n} is the number of observations in the original data and \code{p} is the number of predictors.
#' @param xp a matrix ({`k`} x {`p`}) of synthesized covariates (from previous synthesis steps). \code{k} is the number of already synthesized rows and \code{p} is the number of predictors.
#' @param smoothing smoothing method for numeric variable. See \code{\link[synthpop]{syn.smooth}}.
#' @param proper for proper synthesis ({`proper = TRUE`}) a CART model is fitted to a bootstrapped sample of the original data.
#' @param minbucket the minimum number of observations in any terminal node. See \code{\link[rpart]{rpart.control}} for details.
#' @param cp complexity parameter. Any split that does not decrease the overall lack of fit by a factor of cp is not attempted. Small values of {`cp`} will grow large trees. See \code{\link[rpart]{rpart.control}} for details.
#' @param ctree.logger function(type,data) to handle log messages. Data is structured as JSON.

#'  The following standard log functions have already been defined:
#'  - \link[print_nothing]{print_nothing}
#'  - \link[print_targets]{print_targets}
#'  - \link[print_info]{print_info}
#'  - \link[print_performance]{print_performance}
#'  - \link[print_progress]{print_progress}
#'  - \link[print_info_progress]{print_info_progress}
#'  - \link[print_all]{print_all}
#'
#'  If none of these fits your needs, you can define your own:
#'  \code{custom_logger <- function(type, data) { #custom logging logic}}
#'  \code{s1 <- syn(ods, method = "EncodedCart", ctree.logger = custom_logger)}
#'  \code{type} is the topic of the log message. This can be: "info", "progress", "performance".
#'  \code{data} contains the log output, in JSON format.
#' @return A vector with synthesized values of \code{y}, generated using an encoded CART tree.
#' @details Categorical variables in \code{x} that have many levels (more than 15) are encoded using
#'the \code{\link{encode_categorical}} function. This function chooses the appropriate transformation - mean encoding or principal component analysis - based
#'on the structure of the predictors and the target.
#'
#'These encodings are applied to both \code{x} and \code{xp} to ensure consistency during synthesis.
#'
#'Internally calls: \code{\link{encode_categorical}}, \code{\link[synthpop]{syn.cart}}.
#' @examples
#'# Example usage within the synthpop framework:
#'#s1 <- syn(ods, method = "EncodedCart")
#'
#' s2 <- syn(data_for_synthesis
#'       ,maxfaclevels = Inf
#'       ,method = "EncodedCart"
#'       ,cart.minbucket = 10
#'       ,cart.cp = 0.001
#'       ,ctree.logger = print_all)
#'
#' @seealso \code{\link{encode_categorical}}, \code{\link[synthpop]{syn.cart}}, \code{\link[synthpop]{syn}}
#'
#' @importFrom rpart rpart
#' @export
syn.EncodedCart <- function(y, x, xp, smoothing = "", proper = FALSE,
                            minbucket = 5, cp = 1e-08, ...)
{
  #xp is the already synthesized data from previous variables
  #x contains all predictors for y



  #Lines 11 to 17 in sampler.syn.r in the synthpop package make that one cannot
  # pass arguments to custom synthesis methods.
  # As a work around, we directly access the environment of the calling function
  # to obtain the parameters.
  parent_env <-parent.frame(n = 1)

  calling_params <- get("dots",parent_env)
  #calling_params contains a list of the right side of the assignment when the function is called.
  #If the function is called as syn(...., cart.minbucket = 6), then calling_params contains a named item 'cart.minbucket' with the value 6.
  #If the function is called as
  # A <- 5
  # syn(.....,cart.minbucket = A), then calling_params contains a named item 'cart.minbucket' with the symbol 'A'.
  # A symbol cannot be treated the same way as a value.
  # To deal with both symbols and values, we need to apply the eval function.

  params <- lapply(calling_params,eval)

  if(!("ctree.logger" %in% names(params)) ){
    logger <- function(type,data){}
  }
  else{
    logger <- params$ctree.logger
  }


  params$ctree.logger <- NULL
  names(params)<- gsub("cart[.](.*)","\\1",as.list(names(params)))

  target_name <-get("vname",parent_env)
  logger("info", sprintf("
         'parameters':
         {
              %s
          }
         ",paste0(lapply(names(params),\(x) sprintf("'%s':'%s'",x, params[x])),collapse = ",\n\t\t")))


  logger("progress",sprintf("'target':'%s'",target_name))

  for (i in colnames(x)){
    if(class(x[[i]])=="factor"){
      logger("progress",sprintf("'encoding-feature':'%s','target': '%s'",i,target_name))
      encoded <-encode_categorical(x[[i]],xp[[i]],y,i,logger = logger)

      x = cbind(x,encoded$x)

      x[[i]]<-NULL
      xp = cbind(xp,encoded$xp)
      xp[[i]]<-NULL

    }
  }
  logger("progress",sprintf("'encoding-done':'%s'",target_name))


  start.time <- Sys.time()
  result <- do.call(syn.cart, args = c(list (y = y, x = x , xp = xp),params))
  end.time <- Sys.time()

  synthesis_time <- as.numeric (end.time - start.time , units = "mins")

  logger("performance",sprintf('synth-performance: {
                                    "time":%f,
                                    "rows":%i,
                                    "columns":%i,
                                    "target":%s}',synthesis_time,nrow(x),ncol(x),target_name))
  return(result)



}
