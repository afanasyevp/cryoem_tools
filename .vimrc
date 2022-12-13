syntax on
set mouse=r
set cursorline
hi CursorLine term=bold cterm=bold guibg=Grey40
set ruler
:map <F5> :setlocal spell! spelllang=en_gb<CR>
if $TMUX == ''
    set clipboard+=unnamed
endif

setlocal textwidth=75
setlocal tabstop=4
setlocal shiftwidth=4
setlocal expandtab
set number

function! ResCur()
  if line("'\"") <= line("$")
    normal! g`"
    return 1
  endif
endfunction

augroup resCur
  autocmd!
  autocmd BufWinEnter * call ResCur()
augroup END

set autoindent

" " does not introduce new line when inserting in a long line:
set tw=0
set autoindent

" Move 1 more lines up or down in normal and visual selection modes.
nnoremap K :m .-2<CR>==
nnoremap J :m .+1<CR>==
vnoremap K :m '<-2<CR>gv=gv
vnoremap J :m '>+1<CR>gv=gv
