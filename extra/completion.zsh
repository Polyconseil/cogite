#compdef cogite

_cogite() {
    if [[ ${CURRENT} -eq 2 ]]; then
        COMPREPLY=($(compgen -W "auth ci pr status" -- ${cur}))
    elif [[ ${CURRENT} -eq 3 ]]; then
        local cmd=${COMP_WORDS[1]}
        case ${cmd} in
            auth)
                COMPREPLY=($(compgen -W "add delete" -- ${cur}))
                ;;
            ci)
                COMPREPLY=($(compgen -W "browse" -- ${cur}))
                ;;
            pr)
                COMPREPLY=($(compgen -W "add browse draft merge ready rebase reqreview" -- ${cur}))
                ;;
            status)
                COMPREPLY=($(compgen -W "--poll" -- ${cur}))
                ;;
        esac
    elif [[ ${CURRENT} -gt 3 ]]; then
        local cmd="${COMP_WORDS[1]} ${COMP_WORDS[2]}"
        case ${cmd} in
            "auth add")
                COMPREPLY=($(compgen -W "--help" -- ${cur}))
                ;;
            "auth delete")
                COMPREPLY=($(compgen -W "--help" -- ${cur}))
                ;;
            "ci browse")
                COMPREPLY=($(compgen -W "--help" -- ${cur}))
                ;;
            "pr add")
                COMPREPLY=($(compgen -W "--help --base --draft" -- ${cur}))
                # FIXME (dbaty, 2021-12-04) : I would like to use `_arguments`
                # to have more detailed auto-completion, with this:
                #     _arguments \
                #         '--base[branch where changes should be applied]' \
                #         '--draft[mark as a draft pull request]'
                # ... but I get the following error:
                #    _arguments:34: bad output format specification
                #    _arguments:366: bad math expression: operator expected at `descrs'
                ;;
            "pr browse")
                COMPREPLY=($(compgen -W "--help --browse" -- ${cur}))
                ;;
            "pr draft")
                COMPREPLY=($(compgen -W "--help --base" -- ${cur}))
                ;;
            "pr merge")
                COMPREPLY=($(compgen -W "--help" -- ${cur}))
                ;;
            "pr ready")
                COMPREPLY=($(compgen -W "--help" -- ${cur}))
                ;;
            "pr rebase")
                COMPREPLY=($(compgen -W "--help" -- ${cur}))
                ;;
            "pr reqreview")
                COMPREPLY=($(compgen -W "--help" -- ${cur}))
                ;;
        esac
    fi
}

complete -F _cogite cogite
