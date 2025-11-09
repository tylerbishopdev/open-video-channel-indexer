'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import styles from './page.module.css';

interface Channel {
  channel_handle: string;
  channel_name: string | null;
  video_count: number | null;
  join_date: string | null;
  channel_url: string;
  description: string | null;
  logo_url: string | null;
}

interface Suggestion {
  text: string;
  handle: string;
  video_count: number | null;
}

interface Stats {
  total_channels: number;
  total_videos: number;
  avg_videos_per_channel: string;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Channel[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const autocompleteTimeout = useRef<NodeJS.Timeout>();

  // Load stats on mount
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    if (autocompleteTimeout.current) {
      clearTimeout(autocompleteTimeout.current);
    }

    if (value.trim().length < 2) {
      setShowSuggestions(false);
      return;
    }

    autocompleteTimeout.current = setTimeout(() => {
      fetchAutocomplete(value);
    }, 300);
  };

  const fetchAutocomplete = async (searchQuery: string) => {
    try {
      const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();

      if (data.suggestions && data.suggestions.length > 0) {
        setSuggestions(data.suggestions);
        setShowSuggestions(true);
      } else {
        setShowSuggestions(false);
      }
    } catch (error) {
      console.error('Error fetching autocomplete:', error);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!query.trim()) {
      return;
    }

    setHasSearched(true);
    setShowSuggestions(false);
    setLoading(true);
    setResults([]);

    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();

      if (data.results) {
        setResults(data.results);
      }
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectSuggestion = (text: string) => {
    setQuery(text);
    setShowSuggestions(false);
    setTimeout(() => handleSearch(), 0);
  };

  return (
    <div className={styles.container}>
      <div className={`${styles.header} ${hasSearched ? styles.resultsMode : ''}`}>
        <div className={styles.logo}>
          <Image src="/O.V.png" alt="Open.Video Logo" width={300} height={100} priority />
        </div>
        <div className={styles.subtitle}>Channel Search</div>
      </div>

      <div className={styles.searchWrapper}>
        <form onSubmit={handleSearch} className={styles.searchHeader}>
          <input
            type="text"
            className={styles.searchInput}
            value={query}
            onChange={handleInputChange}
            placeholder="Search channels..."
            autoComplete="off"
          />
          <button type="submit" className={styles.searchButton}>
            <svg className={styles.searchIcon} focusable="false" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
              <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path>
            </svg>
          </button>
        </form>

        {showSuggestions && (
          <div className={styles.autocompleteDropdown}>
            {suggestions.map((suggestion, idx) => (
              <div
                key={idx}
                className={styles.autocompleteItem}
                onClick={() => selectSuggestion(suggestion.text)}
              >
                <span className={styles.autocompleteText}>{suggestion.text}</span>
                <span className={styles.autocompleteMeta}>
                  {suggestion.video_count ? `${suggestion.video_count.toLocaleString()} videos` : ''}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {stats && stats.total_channels > 0 && !hasSearched && (
        <div className={styles.statsBar}>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <div className={styles.statTitle}>Channels Indexed</div>
              <div className={styles.statValue}>{stats.total_channels.toLocaleString()}</div>
            </div>
          </div>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <div className={styles.statTitle}>Total Videos</div>
              <div className={styles.statValue}>{stats.total_videos.toLocaleString()}</div>
            </div>
          </div>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <div className={styles.statTitle}>Avg Videos / Channel</div>
              <div className={styles.statValue}>{stats.avg_videos_per_channel}</div>
            </div>
          </div>
        </div>
      )}

      {loading && <div className={styles.loading}>Searching...</div>}

      {hasSearched && !loading && (
        <>
          {results.length > 0 && (
            <div className={styles.resultStats}>About {results.length} results</div>
          )}

          <div className={styles.results}>
            {results.length > 0 ? (
              results.map((channel, idx) => {
                const name = channel.channel_name || channel.channel_handle;
                const snippet = channel.description || 'No description available';
                const videoCount = channel.video_count ? channel.video_count.toLocaleString() : 'N/A';
                const joinDate = channel.join_date || 'Unknown';

                return (
                  <div key={idx} className={styles.resultItem}>
                    <div className={styles.resultUrl}>
                      <div className={styles.resultFavicon}>📺</div>
                      <div>
                        <div className={styles.resultDomain}>open.video</div>
                        <div style={{ fontSize: '12px', color: '#70757a' }}>@{channel.channel_handle}</div>
                      </div>
                    </div>
                    <div className={styles.resultTitle}>
                      <a href={channel.channel_url} target="_blank" rel="noopener noreferrer">
                        {name}
                      </a>
                    </div>
                    <div className={styles.resultSnippet}>
                      {snippet.substring(0, 200)}{snippet.length > 200 ? '...' : ''}
                    </div>
                    <div className={styles.resultMeta}>
                      {videoCount} videos • Joined {joinDate}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className={styles.noResults}>
                <p>No results found for &quot;<strong>{query}</strong>&quot;</p>
                <p style={{ marginTop: '10px', fontSize: '14px' }}>Try different keywords or check your spelling</p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
