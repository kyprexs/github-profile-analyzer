import requests
print('>>> Running UPDATED GitHub Profile Analyzer!')
import argparse
import json
import csv
from collections import Counter
from analyzer.fetcher import GitHubFetcher
from colorama import Fore, Style, init

init(autoreset=True)


def summarize_repos(repos, fetcher, username, verbose=False):
    """
    Summarize repository statistics for a GitHub user.
    Returns total stars, forks, most used language, and a breakdown of languages.
    """
    total_stars = 0
    total_forks = 0
    language_counter = Counter()
    repo_details = []
    for repo in repos:
        stars = repo.get('stargazers_count', 0)
        forks = repo.get('forks_count', 0)
        lang = repo.get('language') or 'Unknown'
        total_stars += stars
        total_forks += forks
        # Try to get more accurate language stats
        try:
            langs = fetcher.get_repo_languages(username, repo['name'])
            if langs:
                for l, v in langs.items():
                    language_counter[l] += v
            else:
                language_counter[lang] += 1
        except Exception as e:
            if verbose:
                print(f"  [!] Could not fetch languages for {repo['name']}: {e}")
            language_counter[lang] += 1
        repo_details.append({
            'name': repo['name'],
            'stars': stars,
            'forks': forks,
            'language': lang,
            'description': repo.get('description', ''),
            'url': repo.get('html_url', '')
        })
    most_used_lang = language_counter.most_common(1)[0][0] if language_counter else 'Unknown'
    return {
        'total_stars': total_stars,
        'total_forks': total_forks,
        'most_used_language': most_used_lang,
        'repo_details': repo_details,
        'language_breakdown': dict(language_counter)
    }


def print_console(profile, summary, verbose=False):
    """
    Print a visually appealing summary of the GitHub profile and repositories to the console.
    Uses colorama for colored output and shows top 3 languages only.
    """
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*50}")
    print(f"{Fore.GREEN}{Style.BRIGHT}GitHub Profile Analysis for {profile.get('login')}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}👤 Name:        {Fore.WHITE}{profile.get('name')}")
    print(f"{Fore.YELLOW}📦 Public repos:{Fore.WHITE} {profile.get('public_repos')}")
    print(f"{Fore.YELLOW}⭐ Followers:   {Fore.WHITE}{profile.get('followers')}")
    print(f"{Fore.YELLOW}➡️  Following:   {Fore.WHITE}{profile.get('following')}")
    print(f"{Fore.YELLOW}📝 Bio:         {Fore.WHITE}{profile.get('bio')}")
    print(f"\n{Fore.MAGENTA}{'-'*40}")
    print(f"{Fore.BLUE}{Style.BRIGHT}Summary:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}⭐ Total stars:      {Fore.WHITE}{summary['total_stars']}")
    print(f"{Fore.CYAN}🍴 Total forks:      {Fore.WHITE}{summary['total_forks']}")
    print(f"{Fore.CYAN}💻 Most used lang:   {Fore.WHITE}{summary['most_used_language']}")
    # Simplified language breakdown: show top 3 languages
    lang_counts = summary['language_breakdown']
    top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    lang_str = ', '.join([f"{lang} ({count})" for lang, count in top_langs]) if top_langs else 'N/A'
    print(f"{Fore.CYAN}🌈 Top languages:     {Fore.WHITE}{lang_str}")
    print(f"\n{Fore.MAGENTA}{'-'*40}")
    print(f"{Fore.BLUE}{Style.BRIGHT}Repositories:{Style.RESET_ALL}")
    for repo in summary['repo_details']:
        print(f"{Fore.YELLOW}  • {Fore.WHITE}{repo['name']} {Fore.CYAN}(⭐ {repo['stars']}, 🍴 {repo['forks']}, 💻 {repo['language']})")
        if repo['description']:
            print(f"     {Fore.LIGHTBLACK_EX}↳ {repo['description']}")
        if verbose:
            print(f"     {Fore.LIGHTBLUE_EX}🔗 {repo['url']}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")


def export_json(profile, summary, filename):
    """Export the analysis to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({'profile': profile, 'summary': summary}, f, indent=2)


def export_csv(summary, filename):
    """Export the repository summary to a CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Repository', 'Stars', 'Forks', 'Language', 'Description', 'URL'])
        for repo in summary['repo_details']:
            writer.writerow([
                repo['name'], repo['stars'], repo['forks'], repo['language'], repo['description'], repo['url']
            ])


def export_markdown(profile, summary, filename):
    """Export the analysis to a Markdown file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# GitHub Profile Analysis for {profile.get('login')}\n\n")
        f.write(f"**Name:** {profile.get('name')}  \n")
        f.write(f"**Public repos:** {profile.get('public_repos')}  \n")
        f.write(f"**Followers:** {profile.get('followers')}  \n")
        f.write(f"**Following:** {profile.get('following')}  \n")
        f.write(f"**Bio:** {profile.get('bio')}\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Total stars: {summary['total_stars']}\n")
        f.write(f"- Total forks: {summary['total_forks']}\n")
        f.write(f"- Most used language: {summary['most_used_language']}\n")
        # Markdown: show top 3 languages
        lang_counts = summary['language_breakdown']
        top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        lang_str = ', '.join([f"{lang} ({count})" for lang, count in top_langs]) if top_langs else 'N/A'
        f.write(f"- Top languages: {lang_str}\n\n")
        f.write(f"## Repositories\n")
        for repo in summary['repo_details']:
            f.write(f"- **{repo['name']}** (⭐ {repo['stars']}, Forks: {repo['forks']}, Lang: {repo['language']})\n")
            if repo['description']:
                f.write(f"    - Desc: {repo['description']}\n")
            f.write(f"    - URL: {repo['url']}\n")


def main():
    """
    Main entry point for the GitHub Profile Analyzer CLI.
    Parses arguments, fetches data, and prints or exports the analysis.
    """
    parser = argparse.ArgumentParser(description='GitHub Profile Analyzer')
    parser.add_argument('username', nargs='?', help='GitHub username to analyze')
    parser.add_argument('--output', '-o', help='Output file (JSON, CSV, or Markdown based on extension)', default=None)
    parser.add_argument('--format', '-f', help='Output format: console, json, csv, md', default='console')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show more details in output')
    args = parser.parse_args()

    username = args.username
    if not username:
        username = input('Enter GitHub username: ').strip()

    fetcher = GitHubFetcher()
    try:
        profile = fetcher.get_user_profile(username)
        repos = fetcher.get_user_repos(username)
        summary = summarize_repos(repos, fetcher, username, verbose=args.verbose)
        if args.format == 'console':
            print_console(profile, summary, verbose=args.verbose)
        elif args.format == 'json':
            if args.output:
                export_json(profile, summary, args.output)
                print(f"Exported analysis to {args.output}")
            else:
                print(json.dumps({'profile': profile, 'summary': summary}, indent=2))
        elif args.format == 'csv':
            if args.output:
                export_csv(summary, args.output)
                print(f"Exported analysis to {args.output}")
            else:
                print("[!] Please specify an output file for CSV format.")
        elif args.format in ('md', 'markdown'):
            if args.output:
                export_markdown(profile, summary, args.output)
                print(f"Exported analysis to {args.output}")
            else:
                print("[!] Please specify an output file for Markdown format.")
        else:
            print("[!] Unknown format. Use console, json, csv, or md.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("[!] API rate limit exceeded. Please set a GitHub token in your .env file.")
        else:
            print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
    # Prevent window from closing immediately if run by double-clicking (Windows)
    import sys
    if sys.stdin.isatty() and sys.stdout.isatty():
        input("Press Enter to exit...")